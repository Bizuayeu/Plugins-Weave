#!/usr/bin/env python3
"""
Cascade Components - Parameter Object for Cascade Processing
=============================================================

カスケード処理に必要なコンポーネント群をまとめるパラメータオブジェクト。

## 使用デザインパターン

### Parameter Object Pattern
複数のコンストラクタ引数をまとめ、テスト容易性と可読性を向上。

### Factory Method Pattern
from_config()でDigestConfigから必要なコンポーネントを自動構築。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
コンポーネントの集約と構築のみを担当。

Usage:
    from application.shadow.components import CascadeComponents

    # 直接構築
    components = CascadeComponents(
        cascade_processor=processor,
        file_detector=detector,
        file_appender=appender,
        level_hierarchy=hierarchy,
    )

    # DigestConfigから構築
    components = CascadeComponents.from_config(config)

    # Orchestratorに渡す
    orchestrator = CascadeOrchestrator.from_components(components)
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict

from domain.constants import DIGEST_LEVEL_NAMES, build_level_hierarchy
from domain.file_constants import SHADOW_GRAND_DIGEST_FILENAME
from domain.types import LevelHierarchyEntry

if TYPE_CHECKING:
    from application.config import DigestConfig
    from application.shadow.cascade_processor import CascadeProcessor
    from application.shadow.file_appender import FileAppender
    from application.shadow.file_detector import FileDetector

__all__ = ["CascadeComponents"]


@dataclass(frozen=True)
class CascadeComponents:
    """
    カスケード処理に必要なコンポーネント群

    Attributes:
        cascade_processor: データ操作を担当するCascadeProcessor
        file_detector: 新規ファイル検出
        file_appender: ファイル追加処理
        level_hierarchy: レベル間の階層関係

    Example:
        # 直接構築
        components = CascadeComponents(
            cascade_processor=processor,
            file_detector=detector,
            file_appender=appender,
            level_hierarchy=hierarchy,
        )

        # ファクトリメソッドで構築
        components = CascadeComponents.from_config(config)
    """

    cascade_processor: "CascadeProcessor"
    file_detector: "FileDetector"
    file_appender: "FileAppender"
    level_hierarchy: Dict[str, LevelHierarchyEntry]

    @classmethod
    def from_config(cls, config: "DigestConfig") -> "CascadeComponents":
        """
        DigestConfigから必要なコンポーネントを構築

        Args:
            config: DigestConfigインスタンス

        Returns:
            CascadeComponents: 構築されたコンポーネント群

        Example:
            config = DigestConfig(config_dir=Path(".config"))
            components = CascadeComponents.from_config(config)
        """
        from application.shadow.cascade_processor import CascadeProcessor
        from application.shadow.file_appender import FileAppender
        from application.shadow.file_detector import FileDetector
        from application.shadow.placeholder_manager import PlaceholderManager
        from application.shadow.provisional_appender import ProvisionalAppender
        from application.shadow.shadow_io import ShadowIO
        from application.shadow.template import ShadowTemplate
        from application.tracking import DigestTimesTracker

        # レベル階層を構築
        level_hierarchy = build_level_hierarchy()

        # 依存コンポーネントの構築
        times_tracker = DigestTimesTracker(config)
        template = ShadowTemplate(DIGEST_LEVEL_NAMES)
        shadow_digest_file = config.essences_path / SHADOW_GRAND_DIGEST_FILENAME
        shadow_io = ShadowIO(
            shadow_digest_file,
            template_factory=template.get_template,
        )

        # PlaceholderManager
        placeholder_manager = PlaceholderManager()

        # ProvisionalAppender
        provisional_appender = ProvisionalAppender(
            config=config,
            level_hierarchy=level_hierarchy,
        )

        # FileDetector
        file_detector = FileDetector(config, times_tracker)

        # FileAppender
        file_appender = FileAppender(
            shadow_io=shadow_io,
            file_detector=file_detector,
            template=template,
            level_hierarchy=level_hierarchy,
            placeholder_manager=placeholder_manager,
        )

        # CascadeProcessor
        cascade_processor = CascadeProcessor(
            shadow_io=shadow_io,
            file_detector=file_detector,
            template=template,
            level_hierarchy=level_hierarchy,
            file_appender=file_appender,
            provisional_appender=provisional_appender,
        )

        return cls(
            cascade_processor=cascade_processor,
            file_detector=file_detector,
            file_appender=file_appender,
            level_hierarchy=level_hierarchy,
        )
