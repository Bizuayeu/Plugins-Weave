#!/usr/bin/env python3
"""
Shadow Updater
==============

ShadowGrandDigestの更新、カスケード処理を担当（Facade）
"""
from pathlib import Path
from typing import Dict, List, Optional

from domain.types import ShadowDigestData, OverallDigestData, LevelHierarchyEntry
from infrastructure import log_info

from .template import ShadowTemplate
from .file_detector import FileDetector
from .shadow_io import ShadowIO
from .placeholder_manager import PlaceholderManager
from .file_appender import FileAppender
from .cascade_processor import CascadeProcessor


class ShadowUpdater:
    """ShadowGrandDigest更新クラス（Facade）"""

    def __init__(
        self,
        shadow_io: ShadowIO,
        file_detector: FileDetector,
        template: ShadowTemplate,
        level_hierarchy: Dict[str, LevelHierarchyEntry]
    ):
        """
        初期化

        Args:
            shadow_io: ShadowIO インスタンス
            file_detector: FileDetector インスタンス
            template: ShadowTemplate インスタンス
            level_hierarchy: レベル階層情報
        """
        self.shadow_io = shadow_io
        self.file_detector = file_detector
        self.template = template
        self.level_hierarchy = level_hierarchy

        # 内部コンポーネントを初期化
        self._placeholder_manager = PlaceholderManager()
        self._file_appender = FileAppender(
            shadow_io, file_detector, template, level_hierarchy, self._placeholder_manager
        )
        self._cascade_processor = CascadeProcessor(
            shadow_io, file_detector, template, level_hierarchy, self._file_appender
        )

    # =========================================================================
    # パブリックメソッド委譲
    # =========================================================================

    def add_files_to_shadow(self, level: str, new_files: List[Path]) -> None:
        """指定レベルのShadowに新しいファイルを追加（増分更新）"""
        return self._file_appender.add_files_to_shadow(level, new_files)

    def clear_shadow_level(self, level: str) -> None:
        """指定レベルのShadowを初期化"""
        return self._cascade_processor.clear_shadow_level(level)

    def get_shadow_digest_for_level(self, level: str) -> Optional[OverallDigestData]:
        """指定レベルのShadowダイジェストを取得"""
        return self._cascade_processor.get_shadow_digest_for_level(level)

    def promote_shadow_to_grand(self, level: str) -> None:
        """ShadowのレベルをGrandDigestに昇格"""
        return self._cascade_processor.promote_shadow_to_grand(level)

    def update_shadow_for_new_loops(self) -> None:
        """新しいLoopファイルを検出してShadowを増分更新"""
        # Shadowファイルを読み込み（存在しなければ作成）
        self.shadow_io.load_or_create()

        new_files = self.file_detector.find_new_files("weekly")

        if not new_files:
            log_info("No new Loop files found")
            return

        log_info(f"Found {len(new_files)} new Loop file(s):")

        # Shadowに増分追加
        self.add_files_to_shadow("weekly", new_files)

    def cascade_update_on_digest_finalize(self, level: str) -> None:
        """ダイジェスト確定時のカスケード処理（処理3）"""
        return self._cascade_processor.cascade_update_on_digest_finalize(level)
