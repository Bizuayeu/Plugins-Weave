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

import json
import sys
import io
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Windows環境でUTF-8出力を有効化（CLI実行時のみ）
if sys.platform == 'win32' and __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config import DigestConfig, LEVEL_CONFIG, extract_file_number, format_digest_number
from utils import log_info, log_error, log_warning, save_json, get_next_digest_number


class ProvisionalDigestSaver:
    """ProvisionalDigest保存クラス"""

    def __init__(self):
        self.config = DigestConfig()
        self.digests_path = self.config.digests_path

        # レベル設定（共通定数を参照）
        self.level_config = LEVEL_CONFIG


    def get_current_digest_number(self, level: str) -> Optional[int]:
        """
        既存のProvisionalDigestファイルの番号を取得

        Args:
            level: ダイジェストレベル（weekly, monthly等）

        Returns:
            既存のProvisionalファイルがあればその番号、なければNone
        """
        # レベル設定を取得
        level_cfg = self.level_config.get(level)
        if not level_cfg:
            raise ValueError(f"Invalid level: {level}")

        prefix = level_cfg["prefix"]
        provisional_dir = self.config.get_provisional_dir(level)

        # ProvisionalディレクトリのIndividualファイルを検索
        pattern = f"{prefix}[0-9]*_Individual.txt"
        existing_files = list(provisional_dir.glob(pattern))

        if not existing_files:
            return None

        # 最新のファイル番号を取得（共通関数を使用）
        max_num = 0
        for file_path in existing_files:
            result = extract_file_number(file_path.stem)
            if result and result[0] == prefix:
                max_num = max(max_num, result[1])

        return max_num if max_num > 0 else None

    def load_existing_provisional(self, level: str, digest_num: int) -> Optional[Dict[str, Any]]:
        """
        既存のProvisionalDigestファイルを読み込み

        Args:
            level: ダイジェストレベル
            digest_num: ダイジェスト番号

        Returns:
            既存のProvisionalデータ、存在しなければNone
        """
        level_cfg = self.level_config.get(level)
        if not level_cfg:
            raise ValueError(f"Invalid level: {level}")

        # format_digest_number を使用して統一されたファイル名を生成
        filename = f"{format_digest_number(level, digest_num)}_Individual.txt"
        provisional_dir = self.config.get_provisional_dir(level)
        file_path = provisional_dir / filename

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON in {file_path}: {e}")
            raise
        except IOError as e:
            log_error(f"Failed to read {file_path}: {e}")
            raise

    def merge_individual_digests(
        self,
        existing_digests: List[Dict[str, Any]],
        new_digests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        既存と新規のindividual_digestsをマージ（重複はsource_fileで判定し上書き）

        Args:
            existing_digests: 既存のindividual_digestsリスト
            new_digests: 新規のindividual_digestsリスト

        Returns:
            マージされたindividual_digestsリスト

        Raises:
            ValueError: digestにsource_fileキーがない場合
        """
        # 入力検証
        for i, d in enumerate(existing_digests):
            if not isinstance(d, dict) or "source_file" not in d:
                raise ValueError(f"Invalid existing digest at index {i}: missing 'source_file' key")
        for i, d in enumerate(new_digests):
            if not isinstance(d, dict) or "source_file" not in d:
                raise ValueError(f"Invalid new digest at index {i}: missing 'source_file' key")

        # source_fileをキーとした辞書を作成
        merged_dict = {d["source_file"]: d for d in existing_digests}

        # 新規digestsで上書き（重複する場合は最新データを優先）
        for new_digest in new_digests:
            source_file = new_digest["source_file"]
            if source_file in merged_dict:
                log_info(f"Overwriting existing digest: {source_file}")
            merged_dict[source_file] = new_digest

        # リストとして返す
        return list(merged_dict.values())

    def save_provisional(
        self,
        level: str,
        individual_digests: List[Dict[str, Any]],
        append: bool = False
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
        # レベル設定を取得
        level_cfg = self.level_config.get(level)
        if not level_cfg:
            raise ValueError(f"Invalid level: {level}")

        prefix = level_cfg["prefix"]
        digits = level_cfg["digits"]

        # 追加モードの場合、既存番号を使用。なければ警告して新規作成
        if append:
            current_num = self.get_current_digest_number(level)
            if current_num is not None:
                digest_num = current_num
                log_info(f"Appending to existing Provisional: {format_digest_number(level, digest_num)}_Individual.txt")

                # 既存データを読み込み
                existing_data = self.load_existing_provisional(level, digest_num)
                if existing_data:
                    # 型検証
                    if not isinstance(existing_data, dict):
                        log_warning("Invalid existing data format, ignoring")
                        existing_digests = []
                    else:
                        existing_digests = existing_data.get("individual_digests", [])
                        if not isinstance(existing_digests, list):
                            log_warning("Invalid individual_digests format, ignoring")
                            existing_digests = []
                    # マージ（重複は上書き）
                    individual_digests = self.merge_individual_digests(existing_digests, individual_digests)
            else:
                log_warning("--append specified but no existing Provisional found. Creating new file.")
                digest_num = get_next_digest_number(self.digests_path, level)
        else:
            # 通常モード: 次のダイジェスト番号を取得
            digest_num = get_next_digest_number(self.digests_path, level)

        # ファイル名: format_digest_number を使用して統一フォーマット
        formatted_num = format_digest_number(level, digest_num)
        filename = f"{formatted_num}_Individual.txt"
        provisional_dir = self.config.get_provisional_dir(level)
        provisional_dir.mkdir(parents=True, exist_ok=True)
        file_path = provisional_dir / filename

        # ProvisionalDigest構造
        provisional_data = {
            "metadata": {
                "digest_level": level,
                "digest_number": str(digest_num).zfill(digits),  # 純粋な番号のみ
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "individual_digests": individual_digests
        }

        # JSON形式で保存
        save_json(file_path, provisional_data)

        return file_path

    def load_individual_digests(self, input_data: str) -> List[Dict[str, Any]]:
        """
        individual_digestsをJSONファイルまたはJSON文字列から読み込む

        Args:
            input_data: JSONファイルパスまたはJSON文字列

        Returns:
            individual_digestsのリスト

        Raises:
            ValueError: input_dataが空の場合
        """
        # 空文字列チェック
        if not input_data or not input_data.strip():
            raise ValueError("input_data cannot be empty")

        # ファイルパスとして試行
        input_path = Path(input_data)
        if input_path.exists():
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # JSON文字列として解析
            data = json.loads(input_data)

        # dataがリストならそのまま返す
        if isinstance(data, list):
            return data

        # dataが辞書で"individual_digests"キーを持つ場合
        if isinstance(data, dict) and "individual_digests" in data:
            return data["individual_digests"]

        # その他の場合はエラー
        raise ValueError(
            f"Invalid input format. Expected list or dict with 'individual_digests' key. Got: {type(data)}"
        )


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
        """
    )
    parser.add_argument(
        "level",
        choices=["weekly", "monthly", "quarterly", "annual",
                 "triennial", "decadal", "multi_decadal", "centurial"],
        help="ダイジェストレベル"
    )
    parser.add_argument(
        "input_data",
        help="JSONファイルパスまたはJSON文字列"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="既存のProvisionalファイルに追加（新規作成ではなく）"
    )

    args = parser.parse_args()

    try:
        saver = ProvisionalDigestSaver()

        # individual_digestsを読み込み
        individual_digests = saver.load_individual_digests(args.input_data)

        # 空リスト警告
        if len(individual_digests) == 0:
            log_warning("No individual digests to save. Creating empty Provisional file.")

        log_info(f"Loaded {len(individual_digests)} individual digests")

        # ProvisionalDigestを保存
        saved_path = saver.save_provisional(args.level, individual_digests, append=args.append)

        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ ProvisionalDigest保存完了")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")
        print(f"保存先: {saved_path}")
        print(f"個別ダイジェスト数: {len(individual_digests)}")
        if args.append:
            print(f"モード: 追加モード（既存ファイルにマージ）")
        else:
            print(f"モード: 新規作成")
        print("")
        print("次のステップ:")
        print(f"  python finalize_from_shadow.py {args.level} \"タイトル\"")
        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    except FileNotFoundError as e:
        log_error(f"File not found: {e}", exit_code=1)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON format: {e}", exit_code=1)
    except ValueError as e:
        log_error(str(e), exit_code=1)
    except OSError as e:
        log_error(f"File I/O error: {e}", exit_code=1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        log_error(f"Unexpected error: {e}", exit_code=1)


if __name__ == "__main__":
    main()
