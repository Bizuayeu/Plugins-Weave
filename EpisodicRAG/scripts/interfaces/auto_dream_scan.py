#!/usr/bin/env python3
"""
Auto-Dream Memory Scan CLI
===========================

Claude Code auto-memoryファイルをスキャンし、構造化JSONを出力。
digest処理のStep 11（メモリ棚卸し）で使用。

Usage:
    python -m interfaces.auto_dream_scan
    python -m interfaces.auto_dream_scan --project-path "C:\\Users\\anyth\\DEV"

Exit codes:
    0: success (memory found and scanned)
    1: no memory directory found
    2: error during scanning
"""

import argparse
import sys
from pathlib import Path

from application.auto_dream.memory_scanner import MemoryScanner
from domain.file_constants import CONFIG_FILENAME
from infrastructure.auto_dream.memory_discovery import resolve_project_from_path
from infrastructure.config import get_persistent_config_dir
from infrastructure.json_repository import load_json
from interfaces.cli_helpers import output_json

# =============================================================================
# Exit codes
# =============================================================================

EXIT_OK = 0
EXIT_NO_MEMORY = 1
EXIT_ERROR = 2

# =============================================================================
# Status → Exit code mapping
# =============================================================================

_STATUS_EXIT_MAP = {
    "ok": EXIT_OK,
    "no_memory": EXIT_NO_MEMORY,
    "error": EXIT_ERROR,
}


# =============================================================================
# Main
# =============================================================================


def resolve_project_from_config() -> "str | None":
    """
    config.jsonのbase_dirからproject_pathを自動解決

    Returns:
        解決されたproject_path、失敗時はNone
    """
    try:
        config_file = get_persistent_config_dir() / CONFIG_FILENAME
        if not config_file.exists():
            return None

        config = load_json(config_file)
        base_dir = config.get("base_dir", "")
        if not base_dir:
            return None

        resolved = str(Path(base_dir).expanduser().resolve())
        return resolve_project_from_path(resolved)
    except Exception:
        return None


def _setup_windows_utf8() -> None:
    """Windows環境でUTF-8出力を強制"""
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


def main() -> int:
    """
    CLIエントリーポイント

    Returns:
        終了コード（0=ok, 1=no_memory, 2=error）
    """
    parser = argparse.ArgumentParser(
        description="Claude Code auto-memoryファイルをスキャン",
    )
    parser.add_argument(
        "--project-path",
        type=str,
        default=None,
        help="プロジェクトの絶対パス（省略時はconfig.base_dirから自動解決）",
    )
    args = parser.parse_args()

    # Priority cascade: CLI arg > config base_dir > glob-all fallback
    project_path = args.project_path
    if project_path is None:
        project_path = resolve_project_from_config()

    scanner = MemoryScanner(project_path=project_path)
    result = scanner.scan()

    output_json(result)

    return _STATUS_EXIT_MAP.get(result["status"], EXIT_ERROR)


if __name__ == "__main__":
    _setup_windows_utf8()
    sys.exit(main())
