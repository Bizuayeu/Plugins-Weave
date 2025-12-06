#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
last_digest_times.json 更新スクリプト

Loop検出後にlast_processedを直接設定するためのCLI。
finalize_from_shadow.pyを呼ばないパターン1フローで使用。

Usage:
    python -m interfaces.update_digest_times loop 259
    python -m interfaces.update_digest_times weekly 51

Examples:
    # L00259処理完了後
    python -m interfaces.update_digest_times loop 259 --plugin-root /path/to/plugin

    # Weekly 51確定後（通常はfinalize_from_shadowが更新）
    python -m interfaces.update_digest_times weekly 51
"""

import argparse
import io
import sys
from pathlib import Path

# Windows環境でUTF-8出力を有効化（CLI実行時のみ）
if sys.platform == "win32" and __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from application.config import DigestConfig
from application.tracking.digest_times import DigestTimesTracker
from domain.exceptions import EpisodicRAGError
from domain.level_registry import get_level_registry
from infrastructure import get_structured_logger, log_error

_logger = get_structured_logger(__name__)


def main() -> None:
    """メイン処理"""
    registry = get_level_registry()
    valid_levels = ["loop"] + registry.get_level_names()

    parser = argparse.ArgumentParser(
        description="last_digest_times.json更新スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m interfaces.update_digest_times loop 259
  python -m interfaces.update_digest_times weekly 51
        """,
    )
    parser.add_argument(
        "level",
        choices=valid_levels,
        help="ダイジェストレベル（loop, weekly, monthly等）",
    )
    parser.add_argument(
        "last_processed",
        type=int,
        help="設定する番号",
    )
    parser.add_argument(
        "--plugin-root",
        type=str,
        default=None,
        help="Pluginルートパス（デフォルト: 自動検出）",
    )

    args = parser.parse_args()

    try:
        plugin_root = Path(args.plugin_root) if args.plugin_root else None
        config = DigestConfig(plugin_root=plugin_root)
        tracker = DigestTimesTracker(config)

        tracker.update_direct(args.level, args.last_processed)

        print(f"更新完了: {args.level}.last_processed = {args.last_processed}")

    except EpisodicRAGError as e:
        log_error(str(e), exit_code=1)
    except OSError as e:
        log_error(f"File I/O error: {e}", exit_code=1)


if __name__ == "__main__":
    main()
