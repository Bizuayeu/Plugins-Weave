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
    python save_provisional_digest.py weekly '[{"filename":"Loop0001.txt",...}]'
    python save_provisional_digest.py weekly '[{"filename":"Loop0005.txt",...}]' --append
"""

import json
import sys
import io
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Windows環境でUTF-8出力を有効化
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from config import DigestConfig


class ProvisionalDigestSaver:
    """ProvisionalDigest保存クラス"""

    def __init__(self):
        self.config = DigestConfig()
        self.digests_path = self.config.digests_path

        # レベル設定（prefix, 桁数, サブディレクトリ）
        self.level_config = {
            "weekly": {"prefix": "W", "digits": 4, "dir": "1_Weekly"},
            "monthly": {"prefix": "M", "digits": 3, "dir": "2_Monthly"},
            "quarterly": {"prefix": "Q", "digits": 3, "dir": "3_Quarterly"},
            "annual": {"prefix": "A", "digits": 2, "dir": "4_Annual"},
            "triennial": {"prefix": "T", "digits": 2, "dir": "5_Triennial"},
            "decadal": {"prefix": "D", "digits": 2, "dir": "6_Decadal"},
            "multi_decadal": {"prefix": "MD", "digits": 2, "dir": "7_Multi-decadal"},
            "centurial": {"prefix": "C", "digits": 2, "dir": "8_Centurial"}
        }

    def get_next_digest_number(self, level: str) -> int:
        """
        次のダイジェスト番号を取得

        Args:
            level: ダイジェストレベル（weekly, monthly等）

        Returns:
            次のダイジェスト番号（1始まり）
        """
        # レベル設定を取得
        config = self.level_config.get(level)
        if not config:
            raise ValueError(f"Invalid level: {level}")

        prefix = config["prefix"]

        # 既存のRegularDigestファイルを検索
        pattern = f"*{prefix}[0-9]*.txt"
        existing_files = list(self.digests_path.glob(pattern))

        if not existing_files:
            return 1

        # ファイル名から番号を抽出
        max_num = 0
        for file_path in existing_files:
            name = file_path.stem
            # プレフィックスの後の数字部分を抽出
            try:
                # 例: "2025-07-01_W0001_タイトル" → "0001"
                parts = name.split('_')
                for part in parts:
                    if part.startswith(prefix) and len(part) > len(prefix):
                        num_str = part[len(prefix):]
                        # 数字部分のみ抽出
                        num = int(''.join(c for c in num_str if c.isdigit()))
                        max_num = max(max_num, num)
            except (ValueError, IndexError):
                continue

        return max_num + 1

    def get_current_digest_number(self, level: str) -> Optional[int]:
        """
        既存のProvisionalDigestファイルの番号を取得

        Args:
            level: ダイジェストレベル（weekly, monthly等）

        Returns:
            既存のProvisionalファイルがあればその番号、なければNone
        """
        # レベル設定を取得
        config = self.level_config.get(level)
        if not config:
            raise ValueError(f"Invalid level: {level}")

        prefix = config["prefix"]
        provisional_dir = self.get_provisional_dir(level)

        # ProvisionalディレクトリのIndividualファイルを検索
        pattern = f"{prefix}[0-9]*_Individual.txt"
        existing_files = list(provisional_dir.glob(pattern))

        if not existing_files:
            return None

        # 最新のファイル番号を取得
        max_num = 0
        for file_path in existing_files:
            name = file_path.stem
            # プレフィックスの後の数字部分を抽出
            try:
                # 例: "W0001_Individual" → "0001"
                if name.startswith(prefix):
                    num_part = name[len(prefix):].split('_')[0]
                    num = int(''.join(c for c in num_part if c.isdigit()))
                    max_num = max(max_num, num)
            except (ValueError, IndexError):
                continue

        return max_num if max_num > 0 else None

    def get_provisional_dir(self, level: str) -> Path:
        """
        レベルに応じたProvisionalサブディレクトリを取得

        Args:
            level: ダイジェストレベル（weekly, monthly等）

        Returns:
            Provisionalサブディレクトリのパス
        """
        config = self.level_config.get(level)
        if not config:
            raise ValueError(f"Invalid level: {level}")

        provisional_dir = self.digests_path / "Provisional" / config["dir"]
        provisional_dir.mkdir(parents=True, exist_ok=True)
        return provisional_dir

    def load_existing_provisional(self, level: str, digest_num: int) -> Optional[Dict[str, Any]]:
        """
        既存のProvisionalDigestファイルを読み込み

        Args:
            level: ダイジェストレベル
            digest_num: ダイジェスト番号

        Returns:
            既存のProvisionalデータ、存在しなければNone
        """
        config = self.level_config.get(level)
        if not config:
            raise ValueError(f"Invalid level: {level}")

        prefix = config["prefix"]
        digits = config["digits"]
        filename = f"{prefix}{str(digest_num).zfill(digits)}_Individual.txt"
        provisional_dir = self.get_provisional_dir(level)
        filepath = provisional_dir / filename

        if not filepath.exists():
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def merge_individual_digests(
        self,
        existing_digests: List[Dict[str, Any]],
        new_digests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        既存と新規のindividual_digestsをマージ（重複はfilenameで判定し上書き）

        Args:
            existing_digests: 既存のindividual_digestsリスト
            new_digests: 新規のindividual_digestsリスト

        Returns:
            マージされたindividual_digestsリスト
        """
        # filenameをキーとした辞書を作成
        merged_dict = {d["filename"]: d for d in existing_digests}

        # 新規digestsで上書き（重複する場合は最新データを優先）
        for new_digest in new_digests:
            filename = new_digest["filename"]
            if filename in merged_dict:
                print(f"[INFO] Overwriting existing digest: {filename}")
            merged_dict[filename] = new_digest

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
        config = self.level_config.get(level)
        if not config:
            raise ValueError(f"Invalid level: {level}")

        prefix = config["prefix"]
        digits = config["digits"]

        # 追加モードの場合、既存番号を使用。なければ警告して新規作成
        if append:
            current_num = self.get_current_digest_number(level)
            if current_num is not None:
                digest_num = current_num
                print(f"[INFO] Appending to existing Provisional: {prefix}{str(digest_num).zfill(digits)}_Individual.txt")

                # 既存データを読み込み
                existing_data = self.load_existing_provisional(level, digest_num)
                if existing_data:
                    existing_digests = existing_data.get("individual_digests", [])
                    # マージ（重複は上書き）
                    individual_digests = self.merge_individual_digests(existing_digests, individual_digests)
            else:
                print(f"[WARN] --append specified but no existing Provisional found. Creating new file.")
                digest_num = self.get_next_digest_number(level)
        else:
            # 通常モード: 次のダイジェスト番号を取得
            digest_num = self.get_next_digest_number(level)

        # ファイル名: {prefix}{digest_num}_Individual.txt
        filename = f"{prefix}{str(digest_num).zfill(digits)}_Individual.txt"
        provisional_dir = self.get_provisional_dir(level)
        filepath = provisional_dir / filename

        # ProvisionalDigest構造
        provisional_data = {
            "metadata": {
                "digest_level": level,
                "digest_number": str(digest_num).zfill(digits),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "individual_digests": individual_digests
        }

        # JSON形式で保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(provisional_data, f, indent=2, ensure_ascii=False)

        return filepath

    def load_individual_digests(self, input_data: str) -> List[Dict[str, Any]]:
        """
        individual_digestsをJSONファイルまたはJSON文字列から読み込む

        Args:
            input_data: JSONファイルパスまたはJSON文字列

        Returns:
            individual_digestsのリスト
        """
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
  python save_provisional_digest.py weekly '[{"filename":"Loop0001.txt",...}]'
  python save_provisional_digest.py weekly '[{"filename":"Loop0005.txt",...}]' --append
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

        print(f"[INFO] Loaded {len(individual_digests)} individual digests")

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
        print(f"[ERROR] File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON format: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
