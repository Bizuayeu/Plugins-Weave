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
from config import DigestConfig, LEVEL_CONFIG, extract_file_number

# 分割したモジュールをインポート
from grand_digest import GrandDigestManager
from digest_times import DigestTimesTracker
from utils import sanitize_filename, log_info, log_error, log_warning, save_json, get_next_digest_number
from shadow_grand_digest import ShadowGrandDigestManager


class DigestFinalizerFromShadow:
    """ShadowGrandDigestからRegularDigestを作成するファイナライザー（config.py統合版）"""

    def __init__(self, config: Optional[DigestConfig] = None):
        # 設定を読み込み
        if config is None:
            config = DigestConfig()
        self.config = config

        # パスを設定から取得
        self.digests_path = config.digests_path

        # マネージャー初期化
        self.grand_digest_manager = GrandDigestManager(config)
        self.shadow_manager = ShadowGrandDigestManager(config)
        self.times_tracker = DigestTimesTracker(config)

        # レベル設定（共通定数を参照）
        self.level_config = LEVEL_CONFIG

        # レベル→Provisionalサブディレクトリのマッピング（level_configのdirと同じ）
        self.level_to_subdir = {level: config["dir"] for level, config in self.level_config.items()}


    def validate_shadow_content(self, level: str, source_files: list) -> bool:
        """
        ShadowGrandDigestの内容が妥当かチェック

        - source_filesがlist型であること
        - source_filesが空でないこと
        - ファイル名が連番になっていること（警告のみ、継続可能）
        """
        # 型チェック
        if not isinstance(source_files, list):
            log_error(f"source_files must be a list, got {type(source_files).__name__}")
            return False

        if not source_files:
            log_error(f"Shadow digest for level '{level}' has no source files")
            return False

        # ファイル名の型チェック
        for i, filename in enumerate(source_files):
            if not isinstance(filename, str):
                log_error(f"Invalid filename at index {i}: expected str, got {type(filename).__name__}")
                return False

        # ファイル名から番号を抽出（共通関数を使用）
        numbers = []
        for filename in source_files:
            result = extract_file_number(filename)
            if result:
                numbers.append(result[1])
            else:
                log_error(f"Invalid filename format: {filename}")
                return False

        # 連番チェック
        numbers.sort()
        for i in range(len(numbers) - 1):
            if numbers[i + 1] != numbers[i] + 1:
                log_warning("Non-consecutive files detected:")
                print(f"  Files: {source_files}")
                print(f"  Numbers: {numbers}")
                response = input("Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    return False
                break

        log_info(f"Shadow validation passed: {len(source_files)} file(s), range: {numbers[0]}-{numbers[-1]}")
        return True

    def finalize_from_shadow(self, level: str, weave_title: str) -> bool:
        """
        ShadowGrandDigestからRegularDigestを作成

        処理1: RegularDigest作成
        処理2: GrandDigest更新
        処理3: ShadowGrandDigest更新
        処理4: last_digest_times更新
        """
        # 空文字列チェック
        if not weave_title or not weave_title.strip():
            log_error("weave_title cannot be empty")
            return False

        print(f"\n{'='*60}")
        print(f"Finalize Digest from Shadow: {level.upper()}")
        print(f"{'='*60}\n")

        # ===== 処理1: RegularDigest作成 =====
        print(f"[処理1] Creating RegularDigest from Shadow...")

        # Shadowからダイジェスト内容を取得
        shadow_digest = self.shadow_manager.get_shadow_digest_for_level(level)

        if shadow_digest is None:
            log_error(f"No shadow digest found for level: {level}")
            log_info("Run 'python shadow_grand_digest.py' to update shadow first")
            return False

        if not isinstance(shadow_digest, dict):
            log_error(f"Invalid shadow digest format: expected dict, got {type(shadow_digest).__name__}")
            return False

        source_files = shadow_digest.get("source_files", [])

        # Shadow内容のバリデーション
        if not self.validate_shadow_content(level, source_files):
            return False

        log_info(f"Shadow digest contains {len(source_files)} source file(s)")

        # 次のダイジェスト番号を取得
        config = self.level_config[level]
        next_num = get_next_digest_number(self.digests_path, level)
        digest_num = str(next_num).zfill(config["digits"])

        # ファイル名を生成
        sanitized_title = sanitize_filename(weave_title)
        new_digest_name = f"{config['prefix']}{digest_num}_{sanitized_title}"

        # ProvisionalDigestから個別ダイジェストを読み込み
        # レベルに応じたサブディレクトリを取得
        subdir = self.level_to_subdir.get(level)
        provisional_dir = self.digests_path / "Provisional" / subdir

        # ファイル名検索: {prefix}{digest_num}_Individual.txt
        provisional_path = provisional_dir / f"{config['prefix']}{digest_num}_Individual.txt"

        individual_digests = []
        if provisional_path.exists():
            try:
                with open(provisional_path, 'r', encoding='utf-8') as f:
                    provisional_data = json.load(f)
                    if not isinstance(provisional_data, dict):
                        log_error(f"Invalid format in {provisional_path.name}: expected dict")
                        return False
                    individual_digests = provisional_data.get("individual_digests", [])
                log_info(f"Loaded {len(individual_digests)} individual digests from {provisional_path.name}")
            except json.JSONDecodeError as e:
                log_error(f"Invalid JSON in {provisional_path.name}: {e}")
                return False
            except IOError as e:
                log_error(f"Failed to read {provisional_path}: {e}")
                return False

            # ProvisionalDigest削除フラグ（後でクリーンアップ）
            provisional_file_to_delete = provisional_path
        else:
            # Provisionalファイルが存在しない場合、source_filesから自動生成（まだらボケ回避）
            log_info("No Provisional digest found, generating from source files...")
            provisional_file_to_delete = None

            # source_filesからindividual_digestsを自動生成
            source_files = shadow_digest.get("source_files", [])

            for source_file in source_files:
                # ソースファイルの実体を探す
                try:
                    source_dir = self.shadow_manager._get_source_path(level)
                    source_path = source_dir / source_file

                    if source_path.exists() and source_path.suffix == '.txt':
                        with open(source_path, 'r', encoding='utf-8') as f:
                            source_data = json.load(f)
                            overall = source_data.get("overall_digest", {})

                            # individual_digestsエントリ作成
                            individual_entry = {
                                "filename": source_file,
                                "timestamp": overall.get("timestamp", ""),
                                "digest_type": overall.get("digest_type", ""),
                                "keywords": overall.get("keywords", []),
                                "abstract": overall.get("abstract", ""),
                                "impression": overall.get("impression", "")
                            }
                            individual_digests.append(individual_entry)

                            log_info(f"Auto-generated individual digest from {source_file}")
                except json.JSONDecodeError:
                    log_warning(f"Failed to parse {source_file} as JSON")
                except Exception as e:
                    log_warning(f"Error reading {source_file}: {e}")

            log_info(f"Auto-generated {len(individual_digests)} individual digests from source files")

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
            log_warning(f"File already exists: {final_path}")
            try:
                response = input("Overwrite? (y/n): ")
                if response.lower() != 'y':
                    return False
            except EOFError:
                log_info("Non-interactive mode: overwriting existing file")

        # 保存
        try:
            save_json(final_path, regular_digest)
        except IOError as e:
            log_error(f"Failed to save RegularDigest: {e}")
            return False

        log_info(f"RegularDigest saved: {final_path}")

        # ===== 処理2: GrandDigest更新 =====
        print(f"\n[処理2] Updating GrandDigest.txt for {level}")
        overall_digest = regular_digest.get("overall_digest")
        if not overall_digest or not isinstance(overall_digest, dict):
            log_error("RegularDigest has no valid overall_digest")
            return False
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
        self.times_tracker.save(level, source_files)

        # ===== 処理5: ProvisionalDigest削除（クリーンアップ） =====
        if provisional_file_to_delete and provisional_file_to_delete.exists():
            try:
                provisional_file_to_delete.unlink()
                print(f"\n[処理5] Removed Provisional digest after merge: {provisional_file_to_delete.name}")
            except Exception as e:
                log_warning(f"Failed to remove Provisional digest: {e}")

        print(f"\n{'='*60}")
        log_info("Digest finalization completed!")
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
