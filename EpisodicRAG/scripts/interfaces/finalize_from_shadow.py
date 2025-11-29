#!/usr/bin/env python3
"""
EpisodicRAG Digest Finalizer from Shadow (Facade)
==================================================

ShadowGrandDigestの内容からRegularDigestを作成し、
3層のダイジェストシステム（Shadow/Regular/Grand）を更新

## 使用デザインパターン

### Facade Pattern
DigestFinalizerFromShadowクラスは複雑なサブシステム
（GrandDigestManager, ShadowGrandDigestManager, DigestTimesTracker等）
への統一されたインターフェースを提供するFacade。

外部からはfinalize_from_shadow()メソッド1つを呼び出すだけで、
内部の複雑な処理フローが実行される。

### Dependency Injection (コンストラクタインジェクション)
__init__で依存オブジェクト（managers, tracker）をオプション引数で受け取る。
- 本番環境: 引数なしで呼び出し → 内部でデフォルト実装を生成
- テスト環境: モックを注入 → 依存を差し替えてテスト容易に

## SOLID原則の実践

### DIP (Dependency Inversion Principle)
- コンストラクタで抽象（Optional型）を受け取り、具象は内部で生成
- テスト時にモックを注入可能にすることでテスタビリティを向上
- 上位層（Interfaces）が下位層（Application）の具象に直接依存しない

### SRP (Single Responsibility Principle)
- このクラスは「ShadowからRegularDigestを作成」という1つの責務のみ
- 各サブ処理はValidator, Loader, Persistenceに委譲

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

from application.finalize import (
    DigestPersistence,
    ProvisionalLoader,
    RegularDigestBuilder,
    ShadowValidator,
)

# Application層
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.tracking import DigestTimesTracker

# 設定
from config import DigestConfig

# Domain層
from domain.constants import LEVEL_CONFIG, LOG_SEPARATOR
from domain.exceptions import EpisodicRAGError
from domain.file_naming import format_digest_number
from domain.level_registry import get_level_registry

# Infrastructure層
from infrastructure import get_structured_logger, log_error

# Helpers
from interfaces.interface_helpers import get_next_digest_number, sanitize_filename

_logger = get_structured_logger(__name__)


class DigestFinalizerFromShadow:
    """ShadowGrandDigestからRegularDigestを作成するファイナライザー（Facade）"""

    def __init__(
        self,
        config: Optional[DigestConfig] = None,
        grand_digest_manager: Optional[GrandDigestManager] = None,
        shadow_manager: Optional[ShadowGrandDigestManager] = None,
        times_tracker: Optional[DigestTimesTracker] = None,
    ):
        """
        ファイナライザーの初期化

        ## ARCHITECTURE: Dependency Injection (Constructor Injection)
        全ての依存オブジェクトをOptional引数で受け取る。
        - None（デフォルト）: 本番用のデフォルト実装を内部で生成
        - 値を渡す: テスト時にモックやスタブを注入可能

        このパターンにより:
        1. テストでファイルI/Oをモックに置換可能
        2. 本番コードはシンプルに DigestFinalizerFromShadow() で呼び出し
        3. 依存関係が明示的（ドキュメントとして機能）

        Args:
            config: DigestConfig インスタンス（省略時は自動生成）
            grand_digest_manager: GrandDigestManager インスタンス（省略時は自動生成、テスト時にモック注入可能）
            shadow_manager: ShadowGrandDigestManager インスタンス（省略時は自動生成、テスト時にモック注入可能）
            times_tracker: DigestTimesTracker インスタンス（省略時は自動生成、テスト時にモック注入可能）
        """
        # ARCHITECTURE: デフォルト値パターン - Noneなら内部で生成
        if config is None:
            config = DigestConfig()
        self.config = config

        # パスを設定から取得
        self.digests_path = config.digests_path

        # ARCHITECTURE: or パターンでデフォルト実装を遅延生成
        # テスト時は左辺にモックを渡すことで差し替え可能
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
        _logger.info(LOG_SEPARATOR)
        _logger.info(f"Finalize Digest from Shadow: {level.upper()}")
        _logger.info(LOG_SEPARATOR)

        # ===== 処理1: RegularDigest作成 =====
        _logger.info("[Step 1] Creating RegularDigest from Shadow...")

        # Shadowデータの検証と取得（例外を投げる）
        shadow_digest = self._validator.validate_and_get_shadow(level, weave_title)

        # ダイジェスト番号とファイル名を生成（format_digest_number を使用）
        config = self.level_config[level]
        next_num = get_next_digest_number(self.digests_path, level)
        formatted_num = format_digest_number(level, next_num)
        digits = int(str(config["digits"]))  # Ensure int for zfill
        digest_num = str(next_num).zfill(digits)  # 純粋な番号（メタデータ用）
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
        self._persistence.process_cascade_and_cleanup(
            level, source_files, provisional_file_to_delete
        )

        _logger.info(LOG_SEPARATOR)
        _logger.info("Digest finalization completed!")
        _logger.info(LOG_SEPARATOR)


def main() -> None:
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
        """,
    )

    # Registry経由でレベル一覧を動的に取得（OCP準拠）
    registry = get_level_registry()
    parser.add_argument(
        "level",
        choices=registry.get_level_names(),
        help="Digest level to finalize",
    )
    parser.add_argument("weave_title", help="Title decided by Claude")

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
