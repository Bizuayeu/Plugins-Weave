#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ProvisionalDigest保存スクリプト

DigestAnalyzerが生成したindividual_digestsをProvisionalDigestファイルとして保存する。
finalize_from_shadow.pyが読み込むための中間ファイルを作成する。

Usage:
    python save_provisional_digest.py <level> <json_file_or_string> [--append]

Examples:
    python save_provisional_digest.py weekly individual_digests.json
    python save_provisional_digest.py weekly '[{"source_file":"Loop0001.txt",...}]'
    python save_provisional_digest.py weekly '[{"source_file":"Loop0005.txt",...}]' --append
"""

import argparse
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Windows環境でUTF-8出力を有効化（CLI実行時のみ）
if sys.platform == 'win32' and __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Domain層
from domain.exceptions import EpisodicRAGError
from domain.file_naming import format_digest_number
from domain.level_registry import get_level_registry
from domain.types import IndividualDigestData
from domain.version import DIGEST_FORMAT_VERSION

# Infrastructure層
from infrastructure import log_error, log_info, log_warning, save_json

# Config
from config import DigestConfig

# Provisional submodule
from interfaces.provisional import (
    DigestMerger,
    InputLoader,
    ProvisionalFileManager,
)
from interfaces.provisional.validator import validate_provisional_structure

# Helpers
from interfaces.interface_helpers import get_next_digest_number


class ProvisionalDigestSaver:
    """ProvisionalDigest保存クラス"""

    def __init__(self, config: Optional[DigestConfig] = None):
        """
        Initialize the saver.

        Args:
            config: DigestConfig instance (injected for testability)
        """
        self.config = config or DigestConfig()
        self.file_manager = ProvisionalFileManager(self.config)
        self.merger = DigestMerger()

    def save_provisional(
        self, level: str, individual_digests: List[IndividualDigestData], append: bool = False
    ) -> Path:
        """
        ProvisionalDigestファイルを保存

        Args:
            level: ダイジェストレベル
            individual_digests: 個別ダイジェストのリスト
            append: 既存ファイルに追加するか（Trueの場合、既存と新規をマージ）

        Returns:
            保存したファイルのPath
        """
        digits = self.file_manager.get_digits_for_level(level)

        # Determine digest number and handle append mode
        digest_num, individual_digests = self._resolve_digest_number_and_data(
            level, individual_digests, append
        )

        # Build and save the provisional file
        file_path = self.file_manager.get_provisional_path(level, digest_num)
        provisional_data = self._build_provisional_data(level, digest_num, digits, individual_digests)
        save_json(file_path, provisional_data)

        return file_path

    def _resolve_digest_number_and_data(
        self,
        level: str,
        individual_digests: List[IndividualDigestData],
        append: bool,
    ) -> tuple[int, List[IndividualDigestData]]:
        """
        Resolve digest number and merge data if in append mode.

        Returns:
            Tuple of (digest_number, final_individual_digests)
        """
        if not append:
            return get_next_digest_number(self.config.digests_path, level), individual_digests

        # Append mode: try to use existing file
        current_num = self.file_manager.get_current_digest_number(level)

        if current_num is None:
            log_warning("--append specified but no existing Provisional found. Creating new file.")
            return get_next_digest_number(self.config.digests_path, level), individual_digests

        log_info(
            f"Appending to existing Provisional: {format_digest_number(level, current_num)}_Individual.txt"
        )

        # Load and merge with existing data
        existing_data = self.file_manager.load_existing_provisional(level, current_num)
        if existing_data:
            existing_digests = validate_provisional_structure(existing_data)
            individual_digests = self.merger.merge(existing_digests, individual_digests)

        return current_num, individual_digests

    def _build_provisional_data(
        self,
        level: str,
        digest_num: int,
        digits: int,
        individual_digests: List[IndividualDigestData],
    ) -> dict:
        """Build the provisional digest data structure."""
        return {
            "metadata": {
                "digest_level": level,
                "digest_number": str(digest_num).zfill(digits),
                "last_updated": datetime.now().isoformat(),
                "version": DIGEST_FORMAT_VERSION,
            },
            "individual_digests": individual_digests,
        }


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="ProvisionalDigest保存スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python save_provisional_digest.py weekly individual_digests.json
  python save_provisional_digest.py weekly '[{"source_file":"Loop0001.txt",...}]'
  python save_provisional_digest.py weekly '[{"source_file":"Loop0005.txt",...}]' --append
        """,
    )
    # Registry経由でレベル一覧を動的に取得（OCP準拠）
    registry = get_level_registry()
    parser.add_argument(
        "level",
        choices=registry.get_level_names(),
        help="ダイジェストレベル",
    )
    parser.add_argument("input_data", help="JSONファイルパスまたはJSON文字列")
    parser.add_argument(
        "--append", action="store_true", help="既存のProvisionalファイルに追加（新規作成ではなく）"
    )

    args = parser.parse_args()

    try:
        saver = ProvisionalDigestSaver()

        # Load individual digests using InputLoader
        individual_digests = InputLoader.load(args.input_data)

        # Empty list warning
        if len(individual_digests) == 0:
            log_warning("No individual digests to save. Creating empty Provisional file.")

        log_info(f"Loaded {len(individual_digests)} individual digests")

        # Save ProvisionalDigest
        saved_path = saver.save_provisional(args.level, individual_digests, append=args.append)

        log_info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_info("ProvisionalDigest saved successfully")
        log_info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        log_info(f"Path: {saved_path}")
        log_info(f"Individual digests: {len(individual_digests)}")
        if args.append:
            log_info("Mode: Append (merged with existing file)")
        else:
            log_info("Mode: New file")
        log_info("Next step:")
        log_info(f'  python finalize_from_shadow.py {args.level} "TITLE"')
        log_info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    except FileNotFoundError as e:
        log_error(f"File not found: {e}", exit_code=1)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON format: {e}", exit_code=1)
    except EpisodicRAGError as e:
        log_error(str(e), exit_code=1)
    except OSError as e:
        log_error(f"File I/O error: {e}", exit_code=1)


if __name__ == "__main__":
    main()
