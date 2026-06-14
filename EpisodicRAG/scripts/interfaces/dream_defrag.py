#!/usr/bin/env python3
"""
dream-defrag CLI（引く dream＝auto-memory の GC）
===============================================

Claude Code auto-memory（MEMORY.md + memory/*.md）に対する剪定（GC）の
**決定論部分のみ**を提供する CLI。/digest Step 11 の auto_dream_scan（足す dream＝
additive enrichment）と対をなし、本 CLI は欠けた GC 半分を担う。

責務分離（安全要件の中核）:
    本 CLI は「件数を数える・snapshot を取る・索引をディスクに同期する」決定論
    のみを露出する。**何を重複/卒業/上位層DRY と見て剪定するかの判断は持たない**
    ——それは commands/dream-defrag.md のフロー内で Claude=LLM が担う。

サブコマンド:
    scan          メモリ件数を診断し DEFRAG_THRESHOLD 超過を判定（読み取り専用）
    snapshot      剪定前バックアップを作成（auto-memory は git 非追跡＝revert 不能）
    rebuild-index MEMORY.md をディスク現存の memory ファイルに同期（--preview で dry-run）

Usage:
    python -m interfaces.dream_defrag scan
    python -m interfaces.dream_defrag snapshot
    python -m interfaces.dream_defrag rebuild-index --preview
    python -m interfaces.dream_defrag rebuild-index

Exit codes:
    0: success
    1: no memory directory found
    2: error
"""

import argparse
import sys
from pathlib import Path

from application.auto_dream.defrag_scanner import DefragScanner
from domain.file_constants import CONFIG_FILENAME
from infrastructure.auto_dream.index_writer import apply_index, rebuild_index_text
from infrastructure.auto_dream.memory_discovery import resolve_project_from_path
from infrastructure.auto_dream.snapshot_writer import create_snapshot
from infrastructure.config import get_persistent_config_dir
from infrastructure.json_repository import load_json
from interfaces.cli_helpers import output_json

# =============================================================================
# Exit codes / status mapping（auto_dream_scan と統一）
# =============================================================================

EXIT_OK = 0
EXIT_NO_MEMORY = 1
EXIT_ERROR = 2

_STATUS_EXIT_MAP = {
    "ok": EXIT_OK,
    "no_memory": EXIT_NO_MEMORY,
    "error": EXIT_ERROR,
}


# =============================================================================
# Project path 解決（auto_dream_scan と同一挙動）
# =============================================================================


def resolve_project_from_config() -> "str | None":
    """config.json の base_dir から project_path を自動解決"""
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
    """Windows 環境で UTF-8 出力を強制"""
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


# =============================================================================
# サブコマンド実装
# =============================================================================


def _cmd_scan(project_path: "str | None") -> int:
    """メモリ件数を診断（DefragScanResult をそのまま出力）"""
    result = DefragScanner(project_path=project_path).scan()
    output_json(result)
    return _STATUS_EXIT_MAP.get(result["status"], EXIT_ERROR)


def _cmd_snapshot(project_path: "str | None") -> int:
    """剪定前スナップショットを作成"""
    scan = DefragScanner(project_path=project_path).scan()
    if scan["status"] != "ok":
        output_json(
            {"status": scan["status"], "snapshot_path": None, "error": scan["error"]}
        )
        return _STATUS_EXIT_MAP.get(scan["status"], EXIT_ERROR)

    try:
        dest = create_snapshot(Path(scan["memory_dir"]))
        output_json(
            {
                "status": "ok",
                "memory_dir": scan["memory_dir"],
                "snapshot_path": str(dest),
                "error": None,
            }
        )
        return EXIT_OK
    except Exception as e:  # noqa: BLE001 — CLI 境界で error 化
        output_json({"status": "error", "snapshot_path": None, "error": str(e)})
        return EXIT_ERROR


def _cmd_rebuild_index(project_path: "str | None", preview: bool) -> int:
    """MEMORY.md をディスク現存に同期（preview 時は書き込まない）"""
    scan = DefragScanner(project_path=project_path).scan()
    if scan["status"] != "ok":
        output_json(
            {"status": scan["status"], "index_path": None, "error": scan["error"]}
        )
        return _STATUS_EXIT_MAP.get(scan["status"], EXIT_ERROR)

    try:
        memory_dir = Path(scan["memory_dir"])
        new_text = rebuild_index_text(memory_dir)

        if preview:
            output_json(
                {"status": "ok", "preview": True, "index_text": new_text, "error": None}
            )
            return EXIT_OK

        path = apply_index(memory_dir, new_text)
        output_json(
            {
                "status": "ok",
                "preview": False,
                "index_path": str(path),
                "error": None,
            }
        )
        return EXIT_OK
    except Exception as e:  # noqa: BLE001 — CLI 境界で error 化
        output_json({"status": "error", "index_path": None, "error": str(e)})
        return EXIT_ERROR


# =============================================================================
# Main
# =============================================================================


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dream_defrag",
        description="dream-defrag: auto-memory の引く dream（GC）。決定論操作のみ。",
    )

    # 全サブコマンド共通の --project-path（subcommand の後に置けるよう parent 化）
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--project-path",
        type=str,
        default=None,
        help="プロジェクトの絶対パス（省略時は config.base_dir から自動解決）",
    )

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser(
        "scan", parents=[common], help="メモリ件数を診断し threshold 超過を判定"
    )
    sub.add_parser(
        "snapshot", parents=[common], help="剪定前バックアップを作成（必須前提）"
    )
    rebuild = sub.add_parser(
        "rebuild-index",
        parents=[common],
        help="MEMORY.md をディスク現存の memory ファイルに同期",
    )
    rebuild.add_argument(
        "--preview",
        action="store_true",
        help="書き込まず、同期後テキストを出力（dry-run）",
    )
    return parser


def main() -> int:
    """CLI エントリーポイント"""
    parser = _build_parser()
    args = parser.parse_args()

    # Priority cascade: CLI arg > config base_dir > glob-all fallback
    project_path = args.project_path
    if project_path is None:
        project_path = resolve_project_from_config()

    if args.command == "scan":
        return _cmd_scan(project_path)
    if args.command == "snapshot":
        return _cmd_snapshot(project_path)
    if args.command == "rebuild-index":
        return _cmd_rebuild_index(project_path, preview=args.preview)

    parser.print_help()
    return EXIT_ERROR


if __name__ == "__main__":
    _setup_windows_utf8()
    sys.exit(main())
