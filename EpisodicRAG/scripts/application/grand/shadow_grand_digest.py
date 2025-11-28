#!/usr/bin/env python3
"""
ShadowGrandDigest Manager (Facade)
===================================

GrandDigest更新後に作成された新しいコンテンツを保持し、
常に最新の知識にアクセス可能にするシステム

使用方法:
    from application.grand import ShadowGrandDigestManager
    from config import DigestConfig

    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    # 新しいLoopファイルを検出してShadowを更新
    manager.update_shadow_for_new_loops()

    # Weeklyダイジェスト確定時のカスケード処理
    manager.cascade_update_on_digest_finalize("weekly")
"""

from pathlib import Path
from typing import Dict, List, Optional, cast

# 分割したモジュールをインポート
from application.shadow import FileDetector, ShadowIO, ShadowTemplate, ShadowUpdater
from application.tracking import DigestTimesTracker

# Plugin版: config.pyをインポート
from config import DigestConfig
from domain.constants import LEVEL_CONFIG, LEVEL_NAMES, LOG_SEPARATOR, build_level_hierarchy
from domain.types import LevelHierarchyEntry, OverallDigestData
from infrastructure import log_info, log_warning


class ShadowGrandDigestManager:
    """ShadowGrandDigest管理クラス（Facade）"""

    def __init__(self, config: Optional[DigestConfig] = None):
        """
        初期化

        Args:
            config: DigestConfig インスタンス（省略時は自動生成）
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
        self.grand_digest_file = self.essences_path / "GrandDigest.txt"
        self.shadow_digest_file = self.essences_path / "ShadowGrandDigest.txt"

        # レベル設定（共通定数を参照）
        self.levels = LEVEL_NAMES
        self.level_hierarchy = build_level_hierarchy()  # SSoT関数を使用
        self.level_config = LEVEL_CONFIG

        # コンポーネント初期化
        self._template = ShadowTemplate(self.levels)
        self.digest_times_tracker = DigestTimesTracker(config)
        self._detector = FileDetector(config, self.digest_times_tracker)
        self._io = ShadowIO(self.shadow_digest_file, self._template.get_template)
        # Cast level_hierarchy for type compatibility
        hierarchy = cast(Dict[str, LevelHierarchyEntry], self.level_hierarchy)
        self._updater = ShadowUpdater(self._io, self._detector, self._template, hierarchy)

    # ========================================
    # パブリックAPI
    # ========================================

    def add_files_to_shadow(self, level: str, new_files: List[Path]) -> None:
        """指定レベルのShadowに新しいファイルを追加（増分更新）"""
        return self._updater.add_files_to_shadow(level, new_files)

    def clear_shadow_level(self, level: str) -> None:
        """指定レベルのShadowを初期化"""
        self._updater.clear_shadow_level(level)

    def get_shadow_digest_for_level(self, level: str) -> Optional[OverallDigestData]:
        """指定レベルのShadowダイジェストを取得"""
        return self._updater.get_shadow_digest_for_level(level)

    def promote_shadow_to_grand(self, level: str) -> None:
        """ShadowのレベルをGrandDigestに昇格（確認のみ）"""
        self._updater.promote_shadow_to_grand(level)

    def update_shadow_for_new_loops(self) -> None:
        """新しいLoopファイルを検出してShadowを増分更新"""
        self._updater.update_shadow_for_new_loops()

    def cascade_update_on_digest_finalize(self, level: str) -> None:
        """ダイジェスト確定時のカスケード処理"""
        self._updater.cascade_update_on_digest_finalize(level)


def main() -> None:
    """新しいLoopファイルを検出してShadowGrandDigest.weeklyに増分追加"""
    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    log_info(LOG_SEPARATOR)
    log_info("ShadowGrandDigest Update - New Loop Detection")
    log_info(LOG_SEPARATOR)

    # 新しいLoopファイルの検出と追加
    manager.update_shadow_for_new_loops()

    log_info(LOG_SEPARATOR)
    log_info("Placeholder added to ShadowGrandDigest.weekly")
    log_info(LOG_SEPARATOR)
    log_warning("[!] WARNING: Claude analysis required immediately!")
    log_warning("Without analysis, memory fragmentation (madaraboke) occurs.")
    log_info(LOG_SEPARATOR)


if __name__ == "__main__":
    main()
