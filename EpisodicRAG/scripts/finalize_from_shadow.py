#!/usr/bin/env python3
"""
EpisodicRAG Digest Finalizer from Shadow (Facade)
==================================================

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

import argparse
import sys
from typing import Optional

# Plugin版: config.pyをインポート
from config import DigestConfig, LEVEL_CONFIG, format_digest_number

# 分割したモジュールをインポート
from grand_digest import GrandDigestManager
from digest_times import DigestTimesTracker
from utils import sanitize_filename, log_info, log_error, get_next_digest_number
from shadow_grand_digest import ShadowGrandDigestManager
from exceptions import EpisodicRAGError

# 新しいモジュールをインポート
from finalize import ShadowValidator, ProvisionalLoader, RegularDigestBuilder, DigestPersistence


class DigestFinalizerFromShadow:
    """ShadowGrandDigestからRegularDigestを作成するファイナライザー（Facade）"""

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

        # コンポーネントを初期化
        self._validator = ShadowValidator(self.shadow_manager)
        self._loader = ProvisionalLoader(self.config, self.shadow_manager)
        self._persistence = DigestPersistence(
            self.config, self.grand_digest_manager, self.shadow_manager, self.times_tracker
        )

    def validate_shadow_content(self, level: str, source_files: list) -> None:
        """
        ShadowGrandDigestの内容が妥当かチェック（後方互換性のためのラッパー）

        Raises:
            ValidationError: source_filesの形式が不正な場合
        """
        return self._validator.validate_shadow_content(level, source_files)

    def finalize_from_shadow(self, level: str, weave_title: str) -> None:
        """
        ShadowGrandDigestからRegularDigestを作成

        処理1: RegularDigest作成
        処理2: GrandDigest更新
        処理3: ShadowGrandDigest更新
        処理4: last_digest_times更新
        処理5: ProvisionalDigest削除

        Raises:
            ValidationError: 入力データが不正な場合
            DigestError: ダイジェスト処理に失敗した場合
            FileIOError: ファイルI/Oに失敗した場合
        """
        print(f"\n{'='*60}")
        print(f"Finalize Digest from Shadow: {level.upper()}")
        print(f"{'='*60}\n")

        # ===== 処理1: RegularDigest作成 =====
        print(f"[処理1] Creating RegularDigest from Shadow...")

        # Shadowデータの検証と取得（例外を投げる）
        shadow_digest = self._validator.validate_and_get_shadow(level, weave_title)

        # ダイジェスト番号とファイル名を生成（format_digest_number を使用）
        config = self.level_config[level]
        next_num = get_next_digest_number(self.digests_path, level)
        formatted_num = format_digest_number(level, next_num)
        digest_num = str(next_num).zfill(config["digits"])  # 純粋な番号（メタデータ用）
        sanitized_title = sanitize_filename(weave_title)
        new_digest_name = f"{formatted_num}_{sanitized_title}"

        # Provisionalの読み込みまたは自動生成（例外を投げる）
        individual_digests, provisional_file_to_delete = self._loader.load_or_generate(
            level, shadow_digest, digest_num
        )

        # RegularDigest構造を作成
        regular_digest = RegularDigestBuilder.build(
            level, new_digest_name, digest_num, shadow_digest, individual_digests
        )

        # ファイル保存（例外を投げる）
        self._persistence.save_regular_digest(level, regular_digest, new_digest_name)

        # ===== 処理2: GrandDigest更新（例外を投げる） =====
        self._persistence.update_grand_digest(level, regular_digest, new_digest_name)

        # ===== 処理3-5: カスケードとクリーンアップ =====
        source_files = shadow_digest.get("source_files", [])
        self._persistence.process_cascade_and_cleanup(level, source_files, provisional_file_to_delete)

        print(f"\n{'='*60}")
        log_info("Digest finalization completed!")
        print(f"{'='*60}")


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

    try:
        # ファイナライザー実行
        finalizer = DigestFinalizerFromShadow()
        finalizer.finalize_from_shadow(args.level, args.weave_title)
    except EpisodicRAGError as e:
        log_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
