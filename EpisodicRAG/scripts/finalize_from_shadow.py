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
from config import DigestConfig, LEVEL_CONFIG, extract_file_number, format_digest_number

# 分割したモジュールをインポート
from grand_digest import GrandDigestManager
from digest_times import DigestTimesTracker
from utils import sanitize_filename, log_info, log_error, log_warning, save_json, get_next_digest_number
from shadow_grand_digest import ShadowGrandDigestManager


class DigestFinalizerFromShadow:
    """ShadowGrandDigestからRegularDigestを作成するファイナライザー（config.py統合版）"""

    def __init__(
        self,
        config: Optional[DigestConfig] = None,
        grand_digest_manager: Optional[GrandDigestManager] = None,
        shadow_manager: Optional[ShadowGrandDigestManager] = None,
        times_tracker: Optional[DigestTimesTracker] = None
    ):
        """
        ファイナライザーの初期化

        Args:
            config: DigestConfig インスタンス（省略時は自動生成）
            grand_digest_manager: GrandDigestManager インスタンス（省略時は自動生成、テスト時にモック注入可能）
            shadow_manager: ShadowGrandDigestManager インスタンス（省略時は自動生成、テスト時にモック注入可能）
            times_tracker: DigestTimesTracker インスタンス（省略時は自動生成、テスト時にモック注入可能）
        """
        # 設定を読み込み
        if config is None:
            config = DigestConfig()
        self.config = config

        # パスを設定から取得
        self.digests_path = config.digests_path

        # マネージャー初期化（外部から注入可能）
        self.grand_digest_manager = grand_digest_manager or GrandDigestManager(config)
        self.shadow_manager = shadow_manager or ShadowGrandDigestManager(config)
        self.times_tracker = times_tracker or DigestTimesTracker(config)

        # レベル設定（共通定数を参照）
        self.level_config = LEVEL_CONFIG


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

    def _validate_and_get_shadow(self, level: str, weave_title: str) -> Optional[Dict[str, Any]]:
        """
        Shadowデータの検証と取得

        Args:
            level: ダイジェストレベル
            weave_title: タイトル

        Returns:
            検証済みのshadow_digest、失敗時はNone
        """
        # 空文字列チェック
        if not weave_title or not weave_title.strip():
            log_error("weave_title cannot be empty")
            return None

        # Shadowからダイジェスト内容を取得
        shadow_digest = self.shadow_manager.get_shadow_digest_for_level(level)

        if shadow_digest is None:
            log_error(f"No shadow digest found for level: {level}")
            log_info("Run 'python shadow_grand_digest.py' to update shadow first")
            return None

        if not isinstance(shadow_digest, dict):
            log_error(f"Invalid shadow digest format: expected dict, got {type(shadow_digest).__name__}")
            return None

        source_files = shadow_digest.get("source_files", [])

        # Shadow内容のバリデーション
        if not self.validate_shadow_content(level, source_files):
            return None

        log_info(f"Shadow digest contains {len(source_files)} source file(s)")
        return shadow_digest

    def _load_provisional_or_generate(
        self, level: str, shadow_digest: Dict[str, Any], digest_num: str
    ) -> tuple[list, Optional[Path]]:
        """
        Provisionalの読み込みまたはソースから自動生成

        Args:
            level: ダイジェストレベル
            shadow_digest: Shadowダイジェストデータ
            digest_num: ダイジェスト番号（ゼロ埋め済み）

        Returns:
            (individual_digests, provisional_file_to_delete) のタプル
        """
        level_cfg = self.level_config[level]
        provisional_dir = self.config.get_provisional_dir(level)
        provisional_path = provisional_dir / f"{level_cfg['prefix']}{digest_num}_Individual.txt"

        individual_digests = []
        provisional_file_to_delete = None

        if provisional_path.exists():
            try:
                with open(provisional_path, 'r', encoding='utf-8') as f:
                    provisional_data = json.load(f)
                    if not isinstance(provisional_data, dict):
                        log_error(f"Invalid format in {provisional_path.name}: expected dict")
                        return [], None
                    individual_digests = provisional_data.get("individual_digests", [])
                log_info(f"Loaded {len(individual_digests)} individual digests from {provisional_path.name}")
                provisional_file_to_delete = provisional_path
            except json.JSONDecodeError as e:
                log_error(f"Invalid JSON in {provisional_path.name}: {e}")
                return [], None
            except IOError as e:
                log_error(f"Failed to read {provisional_path}: {e}")
                return [], None
        else:
            # Provisionalファイルが存在しない場合、source_filesから自動生成
            log_info("No Provisional digest found, generating from source files...")
            individual_digests = self._generate_individual_digests_from_source(level, shadow_digest)

        return individual_digests, provisional_file_to_delete

    def _generate_individual_digests_from_source(
        self, level: str, shadow_digest: Dict[str, Any]
    ) -> list:
        """
        ソースファイルからindividual_digestsを自動生成（まだらボケ回避）

        Args:
            level: ダイジェストレベル
            shadow_digest: Shadowダイジェストデータ

        Returns:
            individual_digestsのリスト
        """
        individual_digests = []
        source_files = shadow_digest.get("source_files", [])

        for source_file in source_files:
            try:
                source_dir = self.shadow_manager._get_source_path(level)
                source_path = source_dir / source_file

                if source_path.exists() and source_path.suffix == '.txt':
                    with open(source_path, 'r', encoding='utf-8') as f:
                        source_data = json.load(f)
                        overall = source_data.get("overall_digest", {})

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
        return individual_digests

    def _create_regular_digest(
        self,
        level: str,
        new_digest_name: str,
        digest_num: str,
        shadow_digest: Dict[str, Any],
        individual_digests: list
    ) -> Dict[str, Any]:
        """
        RegularDigest構造を作成

        Args:
            level: ダイジェストレベル
            new_digest_name: 新しいダイジェスト名
            digest_num: ダイジェスト番号
            shadow_digest: Shadowダイジェストデータ
            individual_digests: 個別ダイジェストのリスト

        Returns:
            RegularDigest構造体
        """
        source_files = shadow_digest.get("source_files", [])

        return {
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
            "individual_digests": individual_digests
        }

    def _save_regular_digest(
        self, level: str, regular_digest: Dict[str, Any], new_digest_name: str
    ) -> Optional[Path]:
        """
        RegularDigestをファイルに保存

        Args:
            level: ダイジェストレベル
            regular_digest: RegularDigest構造体
            new_digest_name: 新しいダイジェスト名

        Returns:
            保存先のPath、失敗時はNone
        """
        config = self.level_config[level]
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
                    return None
            except EOFError:
                log_info("Non-interactive mode: overwriting existing file")

        # 保存
        try:
            save_json(final_path, regular_digest)
        except IOError as e:
            log_error(f"Failed to save RegularDigest: {e}")
            return None

        log_info(f"RegularDigest saved: {final_path}")
        return final_path

    def _update_grand_digest(self, level: str, regular_digest: Dict[str, Any], new_digest_name: str) -> bool:
        """
        GrandDigestを更新

        Args:
            level: ダイジェストレベル
            regular_digest: RegularDigest構造体
            new_digest_name: 新しいダイジェスト名

        Returns:
            成功時True
        """
        print(f"\n[処理2] Updating GrandDigest.txt for {level}")
        overall_digest = regular_digest.get("overall_digest")
        if not overall_digest or not isinstance(overall_digest, dict):
            log_error("RegularDigest has no valid overall_digest")
            return False
        self.grand_digest_manager.update_digest(level, new_digest_name, overall_digest)
        return True

    def _process_cascade_and_cleanup(
        self, level: str, source_files: list, provisional_file_to_delete: Optional[Path]
    ) -> None:
        """
        カスケード処理とProvisional削除

        Args:
            level: ダイジェストレベル
            source_files: ソースファイルリスト
            provisional_file_to_delete: 削除するProvisionalファイル
        """
        # ShadowGrandDigest更新（カスケード）
        if level != "centurial":
            print(f"\n[処理3] Processing ShadowGrandDigest cascade")
            self.shadow_manager.cascade_update_on_digest_finalize(level)
        else:
            print(f"\n[処理3] Skipped (Centurial is top level, no cascade needed)")

        # last_digest_times更新
        print(f"\n[処理4] Updating last_digest_times.json for {level}")
        self.times_tracker.save(level, source_files)

        # ProvisionalDigest削除（クリーンアップ）
        if provisional_file_to_delete and provisional_file_to_delete.exists():
            try:
                provisional_file_to_delete.unlink()
                print(f"\n[処理5] Removed Provisional digest after merge: {provisional_file_to_delete.name}")
            except Exception as e:
                log_warning(f"Failed to remove Provisional digest: {e}")

    def finalize_from_shadow(self, level: str, weave_title: str) -> bool:
        """
        ShadowGrandDigestからRegularDigestを作成

        処理1: RegularDigest作成
        処理2: GrandDigest更新
        処理3: ShadowGrandDigest更新
        処理4: last_digest_times更新
        処理5: ProvisionalDigest削除
        """
        print(f"\n{'='*60}")
        print(f"Finalize Digest from Shadow: {level.upper()}")
        print(f"{'='*60}\n")

        # ===== 処理1: RegularDigest作成 =====
        print(f"[処理1] Creating RegularDigest from Shadow...")

        # Shadowデータの検証と取得
        shadow_digest = self._validate_and_get_shadow(level, weave_title)
        if shadow_digest is None:
            return False

        # ダイジェスト番号とファイル名を生成（format_digest_number を使用）
        config = self.level_config[level]
        next_num = get_next_digest_number(self.digests_path, level)
        formatted_num = format_digest_number(level, next_num)
        digest_num = str(next_num).zfill(config["digits"])  # 純粋な番号（メタデータ用）
        sanitized_title = sanitize_filename(weave_title)
        new_digest_name = f"{formatted_num}_{sanitized_title}"

        # Provisionalの読み込みまたは自動生成
        individual_digests, provisional_file_to_delete = self._load_provisional_or_generate(
            level, shadow_digest, digest_num
        )

        # RegularDigest構造を作成
        regular_digest = self._create_regular_digest(
            level, new_digest_name, digest_num, shadow_digest, individual_digests
        )

        # ファイル保存
        final_path = self._save_regular_digest(level, regular_digest, new_digest_name)
        if final_path is None:
            return False

        # ===== 処理2: GrandDigest更新 =====
        if not self._update_grand_digest(level, regular_digest, new_digest_name):
            return False

        # ===== 処理3-5: カスケードとクリーンアップ =====
        source_files = shadow_digest.get("source_files", [])
        self._process_cascade_and_cleanup(level, source_files, provisional_file_to_delete)

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
