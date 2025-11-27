#!/usr/bin/env python3
"""
Cascade Processor
=================

ダイジェスト確定時のカスケード処理
"""

from typing import TYPE_CHECKING, Dict, Optional

__all__ = ["CascadeProcessor"]

from application.validators import is_valid_dict
from domain.types import LevelHierarchyEntry, OverallDigestData
from infrastructure import log_info

from .file_detector import FileDetector
from .shadow_io import ShadowIO
from .template import ShadowTemplate

if TYPE_CHECKING:
    from .file_appender import FileAppender


class CascadeProcessor:
    """カスケード処理クラス"""

    def __init__(
        self,
        shadow_io: ShadowIO,
        file_detector: FileDetector,
        template: ShadowTemplate,
        level_hierarchy: Dict[str, LevelHierarchyEntry],
        file_appender: "FileAppender",
    ):
        """
        初期化

        Args:
            shadow_io: ShadowIO インスタンス
            file_detector: FileDetector インスタンス
            template: ShadowTemplate インスタンス
            level_hierarchy: レベル階層情報
            file_appender: FileAppender インスタンス
        """
        self.shadow_io = shadow_io
        self.file_detector = file_detector
        self.template = template
        self.level_hierarchy = level_hierarchy
        self.file_appender = file_appender

    def get_shadow_digest_for_level(self, level: str) -> Optional[OverallDigestData]:
        """
        指定レベルのShadowダイジェストを取得

        finalize_from_shadow.pyで使用: これがRegularDigestの内容になります

        Args:
            level: レベル名

        Returns:
            overall_digestデータ、またはNone
        """
        shadow_data = self.shadow_io.load_or_create()
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        if overall_digest is None or not is_valid_dict(overall_digest):
            log_info(f"No shadow digest for level: {level}")
            return None

        if not overall_digest.get("source_files"):
            log_info(f"No shadow digest for level: {level}")
            return None

        return overall_digest

    def promote_shadow_to_grand(self, level: str) -> None:
        """
        ShadowのレベルをGrandDigestに昇格

        注意: この機能は実際にはfinalize_from_shadow.pyの処理2で
        GrandDigestManagerが実行します。ここでは確認のみ。

        Args:
            level: レベル名
        """
        digest = self.get_shadow_digest_for_level(level)

        if not digest:
            log_info(f"No shadow digest to promote for level: {level}")
            return

        file_count = len(digest.get("source_files", []))
        log_info(f"Shadow digest ready for promotion: {file_count} file(s)")
        # 実際の昇格処理はfinalize_from_shadow.pyで実行される

    def clear_shadow_level(self, level: str) -> None:
        """
        指定レベルのShadowを初期化

        Args:
            level: レベル名
        """
        shadow_data = self.shadow_io.load_or_create()

        # overall_digestを空のプレースホルダーにリセット
        shadow_data["latest_digests"][level]["overall_digest"] = (
            self.template.create_empty_overall_digest()
        )

        self.shadow_io.save(shadow_data)
        log_info(f"Cleared ShadowGrandDigest for level: {level}")

    def cascade_update_on_digest_finalize(self, level: str) -> None:
        """
        ダイジェスト確定時のカスケード処理（処理3）

        処理内容:
        1. 現在のレベルのShadow → Grand に昇格（確認のみ、実際は処理2で完了）
        2. 次のレベルの新しいファイルを検出
        3. 次のレベルのShadowに増分追加
        4. 現在のレベルのShadowをクリア

        Args:
            level: レベル名
        """
        log_info(f"[Step 3] ShadowGrandDigest cascade for level: {level}")

        # 1. Shadow → Grand 昇格の確認
        self.promote_shadow_to_grand(level)

        # 2. 次のレベルの新しいファイルを検出
        next_level = self.level_hierarchy[level]["next"]
        if next_level:
            new_files = self.file_detector.find_new_files(next_level)

            if new_files:
                log_info(f"Found {len(new_files)} new file(s) for {next_level}:")

                # 3. 次のレベルのShadowに増分追加
                self.file_appender.add_files_to_shadow(next_level, new_files)
        else:
            log_info(f"No next level for {level} (top level)")

        # 4. 現在のレベルのShadowをクリア
        self.clear_shadow_level(level)

        log_info(f"[Step 3] Cascade completed for level: {level}")
