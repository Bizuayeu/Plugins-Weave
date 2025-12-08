#!/usr/bin/env python3
"""
ShadowGrandDigest Manager (Facade)
===================================

GrandDigest更新後に作成された新しいコンテンツを保持し、
常に最新の知識にアクセス可能にするシステム

使用方法:
    from application.grand import ShadowGrandDigestManager
    from application.config import DigestConfig

    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    # 新しいLoopファイルを検出してShadowを更新
    manager.update_shadow_for_new_loops()

    # Weeklyダイジェスト確定時のカスケード処理
    manager.cascade_update_on_digest_finalize("weekly")
"""

from pathlib import Path
from typing import List, Optional

# Plugin版: application.configをインポート
from application.config import DigestConfig

# 分割したモジュールをインポート
from application.shadow import FileDetector, ShadowIO, ShadowTemplate, ShadowUpdater
from application.tracking import DigestTimesTracker
from domain.constants import (
    DIGEST_LEVEL_NAMES,
    LEVEL_CONFIG,
    LOG_SEPARATOR,
    build_level_hierarchy,
)
from domain.file_constants import GRAND_DIGEST_FILENAME, SHADOW_GRAND_DIGEST_FILENAME
from domain.types import OverallDigestData, RegularDigestData
from infrastructure import get_structured_logger, log_warning

_logger = get_structured_logger(__name__)


class ShadowGrandDigestManager:
    """ShadowGrandDigest管理クラス（Facade）"""

    def __init__(self, config: Optional[DigestConfig] = None):
        """
        初期化

        Args:
            config: DigestConfig インスタンス（省略時は自動生成）

        Example:
            >>> manager = ShadowGrandDigestManager()
            >>> manager.update_shadow_for_new_loops()
        """
        # 設定を読み込み
        if config is None:
            config = DigestConfig()
        self.config = config

        # パスを設定から取得
        self.digests_path = config.digests_path
        self.loops_path = config.loops_path
        self.essences_path = config.essences_path

        # ファイルパスを設定
        self.grand_digest_file = self.essences_path / GRAND_DIGEST_FILENAME
        self.shadow_digest_file = self.essences_path / SHADOW_GRAND_DIGEST_FILENAME

        # レベル設定（共通定数を参照）
        # ShadowGrandDigestはダイジェスト構造なのでDIGEST_LEVEL_NAMES（loopを除く）を使用
        self.levels = DIGEST_LEVEL_NAMES
        self.level_hierarchy = build_level_hierarchy()  # SSoT関数を使用
        self.level_config = LEVEL_CONFIG

        # コンポーネント初期化
        self._template = ShadowTemplate(self.levels)
        self.digest_times_tracker = DigestTimesTracker(config)
        self._detector = FileDetector(config, self.digest_times_tracker)
        self._io = ShadowIO(self.shadow_digest_file, self._template.get_template)
        self._updater = ShadowUpdater(
            self._io, self._detector, self._template, self.level_hierarchy, config
        )

    # ========================================
    # パブリックAPI
    # ========================================

    def add_files_to_shadow(self, level: str, new_files: List[Path]) -> None:
        """
        指定レベルのShadowに新しいファイルを追加（増分更新）

        Args:
            level: 対象レベル（"weekly", "monthly"等）
            new_files: 追加するファイルパスのリスト

        Note:
            ShadowUpdater.add_files_to_shadow() に委譲。

        Example:
            >>> manager.add_files_to_shadow("weekly", [Path("L00186.txt")])
        """
        return self._updater.add_files_to_shadow(level, new_files)

    def clear_shadow_level(self, level: str) -> None:
        """
        指定レベルのShadowを初期化

        Args:
            level: 対象レベル（"weekly", "monthly"等）

        Note:
            ShadowUpdater.clear_shadow_level() に委譲。

        Example:
            >>> manager.clear_shadow_level("weekly")
        """
        self._updater.clear_shadow_level(level)

    def get_shadow_digest_for_level(self, level: str) -> Optional[OverallDigestData]:
        """
        指定レベルのShadowダイジェストを取得

        Args:
            level: 対象レベル（"weekly", "monthly"等）

        Returns:
            OverallDigestData: Shadowダイジェストデータ
            None: レベルにデータが存在しない場合

        Example:
            >>> digest = manager.get_shadow_digest_for_level("weekly")
            >>> digest["source_files"]
            ["L00186.txt", "L00187.txt"]
        """
        return self._updater.get_shadow_digest_for_level(level)

    def promote_shadow_to_grand(self, level: str) -> None:
        """
        ShadowのレベルをGrandDigestに昇格

        Args:
            level: 対象レベル（"weekly", "monthly"等）

        Note:
            ShadowUpdater.promote_shadow_to_grand() に委譲。

        Example:
            >>> manager.promote_shadow_to_grand("weekly")
        """
        self._updater.promote_shadow_to_grand(level)

    def update_shadow_for_new_loops(self) -> None:
        """
        新しいLoopファイルを検出してShadowを増分更新

        Note:
            ShadowUpdater.update_shadow_for_new_loops() に委譲。
            Loopsディレクトリから新規ファイルを検出し、weekly Shadowに追加。

        Example:
            >>> manager.update_shadow_for_new_loops()
        """
        self._updater.update_shadow_for_new_loops()

    def cascade_update_on_digest_finalize(
        self, level: str, finalized_digest: Optional[RegularDigestData] = None
    ) -> None:
        """
        ダイジェスト確定時のカスケード処理

        Args:
            level: 確定したレベル（"weekly", "monthly"等）
            finalized_digest: 確定したRegularDigest（次レベルProvisional追加用）

        Note:
            ShadowUpdater.cascade_update_on_digest_finalize() に委譲。
            確定レベルをクリアし、上位レベルのShadowを更新。
            finalized_digestが渡された場合、次レベルのProvisionalに追加。

        Example:
            >>> manager.cascade_update_on_digest_finalize("weekly", finalized_digest)
        """
        self._updater.cascade_update_on_digest_finalize(level, finalized_digest)


def main() -> None:
    """新しいLoopファイルを検出してShadowGrandDigest.weeklyに増分追加"""
    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    _logger.info(LOG_SEPARATOR)
    _logger.info("ShadowGrandDigest更新 - 新規Loop検出")
    _logger.info(LOG_SEPARATOR)

    # 新しいLoopファイルの検出と追加
    manager.update_shadow_for_new_loops()

    _logger.info(LOG_SEPARATOR)
    _logger.info("ShadowGrandDigest.weeklyにプレースホルダー追加完了")
    _logger.info(LOG_SEPARATOR)
    log_warning("[!] 警告: Claudeによる即時分析が必要です！")
    log_warning("分析なしでは記憶の断片化（まだらボケ）が発生します。")
    _logger.info(LOG_SEPARATOR)


if __name__ == "__main__":
    main()
