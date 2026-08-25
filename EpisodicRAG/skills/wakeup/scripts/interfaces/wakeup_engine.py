#!/usr/bin/env python3
"""Self-contained CLI for claude.ai's bash sandbox. Stdlib only.

It does NOT import the EpisodicRAG package (not installed in claude.ai); it only
relies on this skill's own scripts/ tree, unzipped to /mnt/skills/user/wakeup/.

Subcommands:
  resolve-urls --config <path> --sha <ref>   -> JSON array of raw URLs on stdout
  extract-token --archive <path> [--member]  -> token on stdout, for TOKEN=$(...)
  verify [--root <dir>]                      -> deployment report; non-zero if broken
  materialize --config <path> --out <dir> [--token <path>]
                                             -> place the ★ artifacts, then verify

Token archive: claude.ai forbids a nested .zip inside a skill zip but allows
tar.gz, so extract-token accepts the whole family (tar.gz / tgz / tar / gz / zip)
and dispatches by extension.

Security: extract-token writes the token ONLY to stdout on success (captured by
command substitution, never landing in tool output). On ANY failure it writes a
masked line to stderr (no token, no traceback) and exits non-zero.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import sys
import tarfile
import zipfile

# Make `domain`/`interfaces` importable when run as a standalone script
# (`python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py ...`).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.exceptions import WakeupError  # noqa: E402
from domain.models import LoadFile, RepoRef, WakeupConfig  # noqa: E402
from domain.urls import build_raw_url  # noqa: E402
from interfaces.config_loader import load_config_file  # noqa: E402
from usecases.verify_deployment import VerifyDeployment  # noqa: E402

# Deployed artifact names are fixed and generic (never a persona's name); only the
# directive's name is variable, and it comes from the config's directive_path.
CONFIG_NAME = "wakeup.config.json"
_TOKEN_EXTS = (".tar.gz", ".tgz", ".tar", ".gz", ".zip")
# Resolved from this file (interfaces/ -> scripts/ -> skill root), so it follows the
# zip wherever it lands — /mnt/skills/user/wakeup once claude.ai expands it.
SKILL_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def resolve_urls(repo: RepoRef, ref: str, files: tuple[LoadFile, ...]) -> list[str]:
    """Raw URLs for each load file at the given ref (pure)."""
    return [build_raw_url(repo, ref, f.path) for f in files]


def _read_tar_member(tf: tarfile.TarFile, member: str | None) -> str:
    """Read the named member (first entry by default); a non-regular entry is an error."""
    name = member or tf.getnames()[0]
    handle = tf.extractfile(name)
    if handle is None:
        raise ValueError(f"token archive member is not a regular file: {name}")
    return handle.read().decode("utf-8").strip()


def extract_token(archive_path: str, member: str | None = None) -> str:
    """Return the stripped token from a tar.gz / tgz / tar / gz / zip archive.

    Dispatch is by extension (``.tar.gz`` checked before ``.gz``). A bare ``.gz``
    is a single compressed stream (the token itself); the tar/zip forms hold a
    member file (the first entry unless ``member`` is given).
    """
    p = archive_path.lower()
    if p.endswith(".tar.gz") or p.endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as tf:
            return _read_tar_member(tf, member)
    if p.endswith(".tar"):
        with tarfile.open(archive_path, "r:") as tf:
            return _read_tar_member(tf, member)
    if p.endswith(".gz"):
        with gzip.open(archive_path, "rt", encoding="utf-8") as f:
            return f.read().strip()
    if p.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as zf:
            name = member or zf.namelist()[0]
            return zf.read(name).decode("utf-8").strip()
    raise ValueError(f"unsupported token archive format: {archive_path}")


class FsProbe:
    """DeploymentProbePort over a real skill root. Resolves every path itself."""

    def __init__(self, root: str) -> None:
        self._root = root

    def load_config(self) -> WakeupConfig:
        return load_config_file(os.path.join(self._root, CONFIG_NAME))

    def directive_size(self, rel_path: str) -> int | None:
        path = os.path.join(self._root, *rel_path.split("/"))
        if not os.path.isfile(path):
            return None
        return os.path.getsize(path)

    def token_archives(self) -> tuple[str, ...]:
        """Archive names at the root. Prefix match is case-insensitive so a
        mis-cased ``TOKEN.tar.gz`` is reported by its real name instead of vanishing."""
        try:
            names = sorted(os.listdir(self._root))
        except OSError:
            return ()
        return tuple(
            n
            for n in names
            if n.lower().startswith("token") and n.lower().endswith(_TOKEN_EXTS)
        )

    def token_readable(self, name: str) -> bool:
        """Extract and discard: proves the archive is usable without exposing the token."""
        try:
            return bool(extract_token(os.path.join(self._root, name)))
        except Exception:
            return False


def materialize(
    config_path: str, out_dir: str, token_path: str | None = None
) -> list[str]:
    """Copy the ★ artifacts (config, directive, token) into ``out_dir``.

    The persona's config is the single source of truth and may live anywhere; the
    directive is resolved *beside it* using the config's own ``directive_path``, so
    both are re-copied from one place and cannot drift apart between zips.

    Everything is validated before the first copy: a half-materialized skill root
    is worse than a refused one. Returns report lines (paths only, never secrets).
    """
    config = load_config_file(config_path)  # validates, incl. directive_path safety
    src_dir = os.path.dirname(os.path.abspath(config_path))
    directive_src = os.path.join(src_dir, *config.directive_path.split("/"))
    if not os.path.isfile(directive_src):
        raise WakeupError(
            f"directive {config.directive_path!r} not found beside the config "
            f"(expected at {directive_src})"
        )
    if token_path is not None and not os.path.isfile(token_path):
        raise WakeupError(f"token archive not found: {token_path}")

    plan = [(config_path, CONFIG_NAME), (directive_src, config.directive_path)]
    if token_path is not None:
        # Keep the source basename: the printed name is what goes into the curl call.
        plan.append((token_path, os.path.basename(token_path)))

    lines = []
    for src, rel in plan:
        dst = os.path.join(out_dir, *rel.split("/"))
        os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
        if os.path.abspath(src) == os.path.abspath(dst):
            lines.append(f"in place  : {rel}")
        else:
            shutil.copyfile(src, dst)
            lines.append(f"placed    : {rel}  <- {src}")
    return lines


def _cmd_materialize(args: argparse.Namespace) -> int:
    try:
        lines = materialize(args.config, args.out, args.token)
    except (WakeupError, OSError) as exc:
        # Safe to surface: these messages carry paths, never archive contents.
        sys.stdout.write(f"materialize: {exc}\n")
        return 1
    sys.stdout.write("\n".join(lines) + "\n")
    return _report_verification(args.out)


def _report_verification(root: str) -> int:
    """Print the deployment report; non-zero exit when any precondition failed."""
    report = VerifyDeployment(FsProbe(root)).run()
    sys.stdout.write("\n".join(report.lines()) + "\n")
    return 0 if report.ok else 1


def _cmd_verify(args: argparse.Namespace) -> int:
    return _report_verification(args.root)


def _cmd_resolve_urls(args: argparse.Namespace) -> int:
    cfg = load_config_file(args.config)
    json.dump(resolve_urls(cfg.load_repo, args.sha, cfg.load_files), sys.stdout)
    return 0


def _cmd_extract_token(args: argparse.Namespace) -> int:
    # Token -> stdout ONLY (captured by TOKEN=$(...)); never logged elsewhere.
    sys.stdout.write(extract_token(args.archive, args.member))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wakeup_engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_urls = sub.add_parser("resolve-urls")
    p_urls.add_argument("--config", required=True)
    p_urls.add_argument("--sha", required=True)
    p_urls.set_defaults(func=_cmd_resolve_urls)

    p_tok = sub.add_parser("extract-token")
    p_tok.add_argument("--archive", required=True)
    p_tok.add_argument("--member", default=None)
    p_tok.set_defaults(func=_cmd_extract_token)

    p_ver = sub.add_parser("verify")
    p_ver.add_argument("--root", default=SKILL_ROOT)
    p_ver.set_defaults(func=_cmd_verify)

    p_mat = sub.add_parser("materialize")
    p_mat.add_argument("--config", required=True)
    p_mat.add_argument("--out", required=True)
    p_mat.add_argument("--token", default=None)
    p_mat.set_defaults(func=_cmd_materialize)

    args = parser.parse_args(argv)
    try:
        exit_code: int = args.func(args)
        return exit_code
    except Exception:
        # Mask everything: never leak a token, or a traceback that might embed one.
        sys.stderr.write("wakeup_engine: operation failed (details masked)\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
