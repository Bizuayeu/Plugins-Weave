#!/usr/bin/env python3
"""Self-contained CLI for claude.ai's bash sandbox. Stdlib only.

It does NOT import the EpisodicRAG package (not installed in claude.ai); it only
relies on this skill's own scripts/ tree, unzipped to /mnt/skills/user/wakeup/.

Subcommands:
  resolve-urls --config <path> --sha <ref>   -> JSON array of raw URLs on stdout
  extract-token --archive <path> [--member]  -> token on stdout, for TOKEN=$(...)

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
import sys
import tarfile
import zipfile

# Make `domain`/`interfaces` importable when run as a standalone script
# (`python /mnt/skills/user/wakeup/scripts/interfaces/wakeup_engine.py ...`).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.models import LoadFile, RepoRef  # noqa: E402
from domain.urls import build_raw_url  # noqa: E402
from interfaces.config_loader import load_config_file  # noqa: E402


def resolve_urls(repo: RepoRef, ref: str, files: tuple[LoadFile, ...]) -> list[str]:
    """Raw URLs for each load file at the given ref (pure)."""
    return [build_raw_url(repo, ref, f.path) for f in files]


def extract_token(archive_path: str, member: str | None = None) -> str:
    """Return the stripped token from a tar.gz / tgz / tar / gz / zip archive.

    Dispatch is by extension (``.tar.gz`` checked before ``.gz``). A bare ``.gz``
    is a single compressed stream (the token itself); the tar/zip forms hold a
    member file (the first entry unless ``member`` is given).
    """
    p = archive_path.lower()
    if p.endswith(".tar.gz") or p.endswith(".tgz"):
        with tarfile.open(archive_path, "r:gz") as tf:
            name = member or tf.getnames()[0]
            return tf.extractfile(name).read().decode("utf-8").strip()
    if p.endswith(".tar"):
        with tarfile.open(archive_path, "r:") as tf:
            name = member or tf.getnames()[0]
            return tf.extractfile(name).read().decode("utf-8").strip()
    if p.endswith(".gz"):
        with gzip.open(archive_path, "rt", encoding="utf-8") as f:
            return f.read().strip()
    if p.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as zf:
            name = member or zf.namelist()[0]
            return zf.read(name).decode("utf-8").strip()
    raise ValueError(f"unsupported token archive format: {archive_path}")


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

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception:
        # Mask everything: never leak a token, or a traceback that might embed one.
        sys.stderr.write("wakeup_engine: operation failed (details masked)\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
