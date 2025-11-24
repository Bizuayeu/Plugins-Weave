#!/usr/bin/env python3
"""
EpisodicRAG Digest Finalizer from Shadow
==========================================

ShadowGrandDigestの内容からRegularDigestを作成し、
3層のダイジェストシステム（Shadow/Regular/Grand）を更新

使用方法：
    python finalize_from_shadow.py LEVEL WEAVE_TITLE

    LEVEL: weekly | monthly | quarterly | annual | triennial | decadal | multi_decadal | centurial
    WEAVE_TITLE: Claudeが決定したタイトル

通常の使用方法：
    `/digest <type>` コマンド経由で自動実行（推奨）

処理フロー：
    【処理1】RegularDigest作成
        - ShadowGrandDigest.{level} の内容を読み込み
        - タイトルに基づいてファイル名を生成
        - RegularDigestファイルとして保存

    【処理2】GrandDigest.txt 更新
        - 作成したRegularDigestをGrandDigestに反映

    【処理3】ShadowGrandDigest.txt 更新（カスケード処理）
        - 現在レベルのShadow → Grandに昇格
        - 次レベルの新しいファイルを検出してShadow更新
        - 現在レベルのShadowをクリア
        - ※ Centurialレベルは最上位のため処理3をスキップ

    【処理4】last_digest_times.json 更新
        - 最終ダイジェスト生成時刻を記録
        - 処理対象ファイルの連番リストを保存
"""

import json
import sys
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Plugin版: config.pyをインポート
from config import DigestConfig

# shadow_grand_digest.pyから相対インポート
from shadow_grand_digest import ShadowGrandDigestManager


class GrandDigestManager:
    """GrandDigest.txt管理クラス（config.py統合版）"""

    def __init__(self, config: DigestConfig):
        self.config = config
        self.grand_digest_file = config.essences_path / "GrandDigest.txt"

    def get_template(self) -> dict:
        """GrandDigest.txtのテンプレートを返す（全8レベル対応）"""
        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "major_digests": {
                "weekly": {
                    "overall_digest": None
                },
                "monthly": {
                    "overall_digest": None
                },
                "quarterly": {
                    "overall_digest": None
                },
                "annual": {
                    "overall_digest": None
                },
                "triennial": {
                    "overall_digest": None
                },
                "decadal": {
                    "overall_digest": None
                },
                "multi_decadal": {
                    "overall_digest": None
                },
                "centurial": {
                    "overall_digest": None
                }
            }
        }

    def load_or_create(self) -> dict:
        """GrandDigest.txtを読み込む。存在しなければテンプレートで作成"""
        if self.grand_digest_file.exists():
            with open(self.grand_digest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("[INFO] GrandDigest.txt not found. Creating new file.")
            template = self.get_template()
            self.save(template)
            return template

    def save(self, data: dict):
        """GrandDigest.txtを保存"""
        with open(self.grand_digest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def update_digest(self, level: str, digest_name: str, overall_digest: dict):
        """指定レベルのダイジェストを更新"""
        grand_data = self.load_or_create()

        if level not in grand_data["major_digests"]:
            print(f"[ERROR] Unknown level: {level}")
            return False

        # overall_digestを更新（完全なオブジェクトとして保存）
        grand_data["major_digests"][level]["overall_digest"] = overall_digest

        # メタデータを更新
        grand_data["metadata"]["last_updated"] = datetime.now().isoformat()

        # 保存
        self.save(grand_data)
        print(f"[INFO] Updated GrandDigest.txt for level: {level}")
        return True


class DigestFinalizerFromShadow:
    """ShadowGrandDigestからRegularDigestを作成するファイナライザー（config.py統合版）"""

    def __init__(self, config: Optional[DigestConfig] = None):
        # 設定を読み込み
        if config is None:
            config = DigestConfig()
        self.config = config

        # パスを設定から取得
        self.digests_path = config.digests_path
        self.last_digest_file = self.config.plugin_root / ".claude-plugin" / "last_digest_times.json"

        # マネージャー初期化
        self.grand_digest_manager = GrandDigestManager(config)
        self.shadow_manager = ShadowGrandDigestManager(config)

        # レベル設定
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

        # レベル→Provisionalサブディレクトリのマッピング（level_configのdirと同じ）
        self.level_to_subdir = {level: config["dir"] for level, config in self.level_config.items()}

    def sanitize_filename(self, title: str) -> str:
        """ファイル名として安全な文字列に変換"""
        sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = sanitized.strip('_')
        if len(sanitized) > 50:
            sanitized = sanitized[:50].rstrip('_')
        return sanitized

    def get_next_digest_number(self, level: str) -> int:
        """次のダイジェスト番号を取得"""
        config = self.level_config[level]
        digest_dir = self.digests_path / config["dir"]

        if not digest_dir.exists():
            return 1

        existing = list(digest_dir.glob(f"{config['prefix']}*.txt"))
        if not existing:
            return 1

        numbers = []
        for f in existing:
            match = re.search(rf"{config['prefix']}(\d+)_", f.stem)
            if match:
                numbers.append(int(match.group(1)))

        return max(numbers) + 1 if numbers else 1

    def load_last_digest_times(self) -> dict:
        """最終ダイジェスト生成時刻を読み込む（存在しなければテンプレートから初期化）"""
        if self.last_digest_file.exists():
            with open(self.last_digest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # テンプレートから初期化
            template_file = self.config.plugin_root / ".claude-plugin" / "last_digest_times.template.json"
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                # テンプレートをコピーして保存
                with open(self.last_digest_file, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                print(f"[INFO] Initialized last_digest_times.json from template")
                return template
            else:
                # テンプレートがない場合は空の階層的フォーマット
                levels = list(self.level_config.keys())
                return {level: {"timestamp": "", "last_processed": None} for level in levels}

    def extract_file_numbers(self, level: str, input_files: list) -> list:
        """ファイル名から連番を抽出（プレフィックス付き、ゼロ埋め維持）"""
        if not input_files:
            return []

        numbers = []
        for file in input_files:
            # Loopファイルの場合: Loop0181_xxx.txt → "Loop0181"
            match = re.search(r'(Loop\d+)', file)
            if match:
                numbers.append(match.group(1))
            else:
                # Digestファイルの場合: W0037_xxx.txt → "W0037", MD01_xxx.txt → "MD01", C01_xxx.txt → "C01"
                for prefix in ['W', 'M', 'Q', 'A', 'T', 'D', 'MD', 'C']:
                    match = re.search(rf'({prefix}\d+)', file)
                    if match:
                        numbers.append(match.group(1))
                        break

        return sorted(numbers)

    def save_last_digest_time(self, level: str, input_files: list = None):
        """最終ダイジェスト生成時刻と最新処理済みファイル番号を保存"""
        times = self.load_last_digest_times()

        # 連番を抽出
        file_numbers = self.extract_file_numbers(level, input_files)

        # 最後の要素のみを保存
        last_file = file_numbers[-1] if file_numbers else None

        # 保存
        times[level] = {
            "timestamp": datetime.now().isoformat(),
            "last_processed": last_file
        }

        with open(self.last_digest_file, 'w', encoding='utf-8') as f:
            json.dump(times, f, indent=2, ensure_ascii=False)

        print(f"[INFO] Updated last_digest_times.json for level: {level}")
        if last_file:
            print(f"[INFO] Last processed: {last_file}")

    def validate_shadow_content(self, level: str, source_files: list) -> bool:
        """
        ShadowGrandDigestの内容が妥当かチェック

        - source_filesが空でないこと
        - ファイル名が連番になっていること（警告のみ、継続可能）
        """
        if not source_files:
            print(f"[ERROR] Shadow digest has no source files")
            return False

        # ファイル名から番号を抽出
        numbers = []
        for filename in source_files:
            match = re.search(r'(Loop|[WMQATD])(\d+)', filename)
            if match:
                numbers.append(int(match.group(2)))
            else:
                print(f"[ERROR] Invalid filename format: {filename}")
                return False

        # 連番チェック
        numbers.sort()
        for i in range(len(numbers) - 1):
            if numbers[i + 1] != numbers[i] + 1:
                print(f"[WARNING] Non-consecutive files detected:")
                print(f"  Files: {source_files}")
                print(f"  Numbers: {numbers}")
                response = input("Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    return False
                break

        print(f"[OK] Shadow validation passed: {len(source_files)} file(s), range: {numbers[0]}-{numbers[-1]}")
        return True

    def finalize_from_shadow(self, level: str, weave_title: str) -> bool:
        """
        ShadowGrandDigestからRegularDigestを作成

        処理1: RegularDigest作成
        処理2: GrandDigest更新
        処理3: ShadowGrandDigest更新
        処理4: last_digest_times更新
        """
        print(f"\n{'='*60}")
        print(f"Finalize Digest from Shadow: {level.upper()}")
        print(f"{'='*60}\n")

        # ===== 処理1: RegularDigest作成 =====
        print(f"[処理1] Creating RegularDigest from Shadow...")

        # Shadowからダイジェスト内容を取得
        shadow_digest = self.shadow_manager.get_shadow_digest_for_level(level)

        if not shadow_digest:
            print(f"[ERROR] No shadow digest found for level: {level}")
            print(f"[HINT] Run 'python shadow_grand_digest.py' to update shadow first")
            return False

        source_files = shadow_digest.get("source_files", [])

        # Shadow内容のバリデーション
        if not self.validate_shadow_content(level, source_files):
            return False

        print(f"[INFO] Shadow digest contains {len(source_files)} source file(s)")

        # 次のダイジェスト番号を取得
        config = self.level_config[level]
        next_num = self.get_next_digest_number(level)
        digest_num = str(next_num).zfill(config["digits"])

        # ファイル名を生成
        sanitized_title = self.sanitize_filename(weave_title)
        new_digest_name = f"{config['prefix']}{digest_num}_{sanitized_title}"

        # ProvisionalDigestから個別ダイジェストを読み込み
        # レベルに応じたサブディレクトリを取得
        subdir = self.level_to_subdir.get(level)
        provisional_dir = self.digests_path / "Provisional" / subdir

        # ファイル名検索: {prefix}{digest_num}_Individual.txt
        provisional_path = provisional_dir / f"{config['prefix']}{digest_num}_Individual.txt"

        individual_digests = []
        if provisional_path.exists():
            with open(provisional_path, 'r', encoding='utf-8') as f:
                provisional_data = json.load(f)
                individual_digests = provisional_data.get("individual_digests", [])
            print(f"[INFO] Loaded {len(individual_digests)} individual digests from {provisional_path.name}")

            # ProvisionalDigest削除フラグ（後でクリーンアップ）
            provisional_file_to_delete = provisional_path
        else:
            print(f"[INFO] No Provisional digest found, individual_digests will be empty")
            provisional_file_to_delete = None

        # RegularDigestの構造を作成
        regular_digest = {
            "metadata": {
                "digest_level": level,
                "digest_number": digest_num,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            },
            "overall_digest": {
                "name": new_digest_name,
                "timestamp": datetime.now().isoformat(),
                "source_files": source_files,
                "digest_type": shadow_digest.get("digest_type", "統合"),
                "keywords": shadow_digest.get("keywords", []),
                "abstract": shadow_digest.get("abstract", ""),
                "impression": shadow_digest.get("impression", "")
            },
            "individual_digests": individual_digests  # ProvisionalDigestから読み込み
        }

        # ファイルパスを決定
        target_dir = self.digests_path / config["dir"]
        target_dir.mkdir(parents=True, exist_ok=True)
        final_filename = f"{new_digest_name}.txt"
        final_path = target_dir / final_filename

        # 既存ファイルチェック
        if final_path.exists():
            print(f"[WARNING] File already exists: {final_path}")
            try:
                response = input("Overwrite? (y/n): ")
                if response.lower() != 'y':
                    return False
            except EOFError:
                print("[INFO] Non-interactive mode: overwriting existing file")

        # 保存
        with open(final_path, 'w', encoding='utf-8') as f:
            json.dump(regular_digest, f, ensure_ascii=False, indent=2)

        print(f"[SUCCESS] RegularDigest saved: {final_path}")

        # ===== 処理2: GrandDigest更新 =====
        print(f"\n[処理2] Updating GrandDigest.txt for {level}")
        overall_digest = regular_digest.get("overall_digest", {})
        self.grand_digest_manager.update_digest(level, new_digest_name, overall_digest)

        # ===== 処理3: ShadowGrandDigest更新 =====
        # Centurialレベルは最上位のため処理3をスキップ
        if level != "centurial":
            print(f"\n[処理3] Processing ShadowGrandDigest cascade")
            self.shadow_manager.cascade_update_on_digest_finalize(level)
        else:
            print(f"\n[処理3] Skipped (Centurial is top level, no cascade needed)")

        # ===== 処理4: last_digest_times更新 =====
        print(f"\n[処理4] Updating last_digest_times.json for {level}")
        self.save_last_digest_time(level, source_files)

        # ===== 処理5: ProvisionalDigest削除（クリーンアップ） =====
        if provisional_file_to_delete and provisional_file_to_delete.exists():
            try:
                provisional_file_to_delete.unlink()
                print(f"\n[処理5] Removed Provisional digest after merge: {provisional_file_to_delete.name}")
            except Exception as e:
                print(f"\n[WARNING] Failed to remove Provisional digest: {e}")

        print(f"\n{'='*60}")
        print(f"[SUCCESS] Digest finalization completed!")
        print(f"{'='*60}")

        return True


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description="Finalize digest from ShadowGrandDigest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script creates a RegularDigest from ShadowGrandDigest content:

Process flow:
  1. Read Shadow digest content
  2. Create RegularDigest file
  3. Update GrandDigest
  4. Cascade update ShadowGrandDigest
  5. Update last_digest_times.json

Example:
  python finalize_from_shadow.py weekly "知性射程理論と協働AI実現"
        """
    )

    parser.add_argument("level",
                       choices=["weekly", "monthly", "quarterly", "annual", "triennial", "decadal", "multi_decadal", "centurial"],
                       help="Digest level to finalize")
    parser.add_argument("weave_title",
                       help="Title decided by Claude")

    args = parser.parse_args()

    # ファイナライザー実行
    finalizer = DigestFinalizerFromShadow()
    success = finalizer.finalize_from_shadow(args.level, args.weave_title)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
