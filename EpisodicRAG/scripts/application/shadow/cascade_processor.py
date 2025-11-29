#!/usr/bin/env python3
"""
Cascade Processor
=================

ダイジェスト確定時の階層的カスケード処理を担当するアプリケーション層モジュール。

ダイジェストがfinalize（確定）された際、次の階層レベルへの
自動的な伝播処理を実行する。これにより8階層メモリシステム
（Weekly→Monthly→...→Centurial）の階層的な情報集約が実現される。

Usage:
    from application.shadow import CascadeProcessor

    processor = CascadeProcessor(
        shadow_io=shadow_io,
        file_detector=file_detector,
        template=template,
        level_hierarchy=LEVEL_HIERARCHY,
        file_appender=file_appender
    )

    # ダイジェスト確定後にカスケード処理を実行
    processor.cascade_update_on_digest_finalize("weekly")

Design Pattern:
    - Chain of Responsibility: レベル間の連鎖的な処理
    - Dependency Injection: 各コンポーネントを注入して構成

Related Modules:
    - application.shadow.shadow_io: ShadowGrandDigestのI/O
    - application.shadow.file_detector: 新規ファイル検出
    - application.shadow.file_appender: ファイル追加処理
    - interfaces.finalize_from_shadow: 確定処理の起点

Note:
    カスケード処理は以下の順序で実行される：
    1. 現在レベルのShadow→Grand昇格確認
    2. 次レベルの新規ファイル検出
    3. 次レベルのShadowに増分追加
    4. 現在レベルのShadowをクリア
"""

from typing import TYPE_CHECKING, Dict, Optional

__all__ = ["CascadeProcessor"]

from domain.types import LevelHierarchyEntry, OverallDigestData
from domain.validators import is_valid_overall_digest
from infrastructure import get_structured_logger

from .file_detector import FileDetector
from .shadow_io import ShadowIO
from .template import ShadowTemplate

if TYPE_CHECKING:
    from .file_appender import FileAppender

# 構造化ロガー
_logger = get_structured_logger(__name__)


class CascadeProcessor:
    """
    ダイジェスト確定時のカスケード処理を実行するクラス。

    このクラスはChain of Responsibilityパターンを採用し、
    あるレベルのダイジェストが確定した際に、次のレベルへの
    自動的な更新処理を連鎖的に実行する。

    Attributes:
        shadow_io: ShadowGrandDigestの読み書きを担当
        file_detector: 新規ファイル検出を担当
        template: テンプレート生成を担当
        level_hierarchy: レベル間の階層関係情報
        file_appender: ファイル追加処理を担当

    Example:
        >>> processor = CascadeProcessor(
        ...     shadow_io, file_detector, template, hierarchy, appender
        ... )
        >>> processor.cascade_update_on_digest_finalize("weekly")
        # weekly確定 → monthlyのShadowに新規ファイル追加
    """

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

        finalize_from_shadow.pyで使用: ShadowGrandDigestからoverall_digestを取得

        Args:
            level: レベル名

        Returns:
            overall_digestデータ、またはNone
        """
        shadow_data = self.shadow_io.load_or_create()
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        _logger.state("get_shadow_digest_for_level", level=level)
        _logger.validation(
            "overall_digest", is_valid=is_valid_overall_digest(overall_digest)
        )

        if not is_valid_overall_digest(overall_digest):
            _logger.info(f"No shadow digest for level: {level}")
            return None

        # is_valid_overall_digest は TypeGuard なので、
        # この時点で overall_digest は OverallDigestData 型に絞り込まれている
        _logger.validation("source_files", count=len(overall_digest["source_files"]))
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
            _logger.info(f"No shadow digest to promote for level: {level}")
            return

        file_count = len(digest.get("source_files", []))
        _logger.info(f"Shadow digest ready for promotion: {file_count} file(s)")
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
        _logger.info(f"Cleared ShadowGrandDigest for level: {level}")

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
        _logger.info(f"[Step 3] ShadowGrandDigest cascade for level: {level}")
        _logger.state("cascade_update", starting_for_level=level)

        # 1. Shadow → Grand 昇格の確認
        self.promote_shadow_to_grand(level)

        # 2. 次のレベルの新しいファイルを検出
        next_level = self.level_hierarchy[level]["next"]
        _logger.decision("next_level", level=next_level)

        if next_level:
            new_files = self.file_detector.find_new_files(next_level)
            _logger.file_op(f"find_new_files({next_level})", found=len(new_files))

            if new_files:
                _logger.info(f"Found {len(new_files)} new file(s) for {next_level}:")
                file_names = [f.name for f in new_files[:5]]
                suffix = "..." if len(new_files) > 5 else ""
                _logger.file_op("new_files", names=f"{file_names}{suffix}")

                # 3. 次のレベルのShadowに増分追加
                self.file_appender.add_files_to_shadow(next_level, new_files)
        else:
            _logger.info(f"No next level for {level} (top level)")

        # 4. 現在のレベルのShadowをクリア
        self.clear_shadow_level(level)

        _logger.info(f"[Step 3] Cascade completed for level: {level}")
