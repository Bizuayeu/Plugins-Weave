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

from application.auto_dream.memory_scanner import MemoryScanner
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
        help="プロジェクトの絶対パス（省略時は全プロジェクト検索）",
    )
    args = parser.parse_args()

    scanner = MemoryScanner(project_path=args.project_path)
    result = scanner.scan()

    output_json(result)

    return _STATUS_EXIT_MAP.get(result["status"], EXIT_ERROR)


if __name__ == "__main__":
    _setup_windows_utf8()
    sys.exit(main())
