#!/usr/bin/env python3
"""Self-contained CLI for claude.ai's bash sandbox. Stdlib only.

It does NOT import the EpisodicRAG package (not installed in claude.ai); it only
relies on this skill's own scripts/ tree, which is unzipped to /mnt/skills/user/wakeup/.

Subcommands:
  resolve-urls --config <path> --sha <ref>   -> JSON array of raw URLs on stdout
  extract-token --zip <path> [--member NAME] -> token on stdout, for TOKEN=$(...)

Security: extract-token writes the token ONLY to stdout on success (captured by
command substitution, so it never lands in tool output). On ANY failure it writes
a masked line to stderr (no token, no traceback) and exits non-zero.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
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


def extract_token_from_zip(zip_path: str, member: str | None = None) -> str:
    """Return the stripped token stored in a zip (first member by default)."""
    with zipfile.ZipFile(zip_path) as zf:
        name = member or zf.namelist()[0]
        return zf.read(name).decode("utf-8").strip()


def _cmd_resolve_urls(args: argparse.Namespace) -> int:
    cfg = load_config_file(args.config)
    json.dump(resolve_urls(cfg.public_repo, args.sha, cfg.load_files), sys.stdout)
    return 0


def _cmd_extract_token(args: argparse.Namespace) -> int:
    # Token -> stdout ONLY (captured by TOKEN=$(...)); never logged elsewhere.
    sys.stdout.write(extract_token_from_zip(args.zip, args.member))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wakeup_engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_urls = sub.add_parser("resolve-urls")
    p_urls.add_argument("--config", required=True)
    p_urls.add_argument("--sha", required=True)
    p_urls.set_defaults(func=_cmd_resolve_urls)

    p_tok = sub.add_parser("extract-token")
    p_tok.add_argument("--zip", required=True)
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
