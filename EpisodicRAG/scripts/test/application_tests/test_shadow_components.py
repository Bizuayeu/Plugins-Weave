#!/usr/bin/env python3
"""
Shadow Components Tests
=======================

CascadeComponentsパラメータオブジェクトのテスト。

TDD Red Phase: パラメータオブジェクトのテスト。
"""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from application.config import DigestConfig
    from test.test_helpers import TempPluginEnvironment


@pytest.mark.unit
class TestCascadeComponents:
    """CascadeComponentsパラメータオブジェクトのテスト"""

    def test_creates_with_all_fields(self) -> None:
        """全フィールドを指定してCascadeComponentsを生成できる"""
        from application.shadow.components import CascadeComponents

        # モックを作成
        cascade_processor = MagicMock()
        file_detector = MagicMock()
        file_appender = MagicMock()
        level_hierarchy = {"weekly": {"next": "monthly", "threshold": 4}}

        components = CascadeComponents(
            cascade_processor=cascade_processor,
            file_detector=file_detector,
            file_appender=file_appender,
            level_hierarchy=level_hierarchy,
        )

        assert components.cascade_processor is cascade_processor
        assert components.file_detector is file_detector
        assert components.file_appender is file_appender
        assert components.level_hierarchy == level_hierarchy

    def test_is_frozen_dataclass(self) -> None:
        """CascadeComponentsがfrozen dataclassであることを確認"""
        from application.shadow.components import CascadeComponents

        cascade_processor = MagicMock()
        file_detector = MagicMock()
        file_appender = MagicMock()
        level_hierarchy = {}

        components = CascadeComponents(
            cascade_processor=cascade_processor,
            file_detector=file_detector,
            file_appender=file_appender,
            level_hierarchy=level_hierarchy,
        )

        # frozen dataclassは属性を変更できない
        with pytest.raises(AttributeError):
            components.cascade_processor = MagicMock()  # type: ignore[misc]


@pytest.mark.integration
@pytest.mark.skip(reason="from_config requires additional DigestConfig properties - future enhancement")
class TestCascadeComponentsFromConfig:
    """CascadeComponents.from_configファクトリメソッドのテスト

    Note: from_config()はDigestConfigに追加のプロパティが必要なため、
    現時点ではスキップ。将来の拡張として残す。
    """

    def test_creates_from_config(self, digest_config: "DigestConfig") -> None:
        """DigestConfigからCascadeComponentsを生成できる"""
        from application.shadow.components import CascadeComponents

        # ファクトリメソッドでコンポーネントを生成
        components = CascadeComponents.from_config(digest_config)

        # 全てのコンポーネントが生成されていることを確認
        assert components.cascade_processor is not None
        assert components.file_detector is not None
        assert components.file_appender is not None
        assert components.level_hierarchy is not None
        assert isinstance(components.level_hierarchy, dict)


@pytest.mark.unit
class TestCascadeOrchestratorWithComponents:
    """CascadeOrchestratorがCascadeComponentsを受け入れることを確認"""

    def test_orchestrator_accepts_components(self) -> None:
        """CascadeOrchestratorがCascadeComponentsを受け入れる"""
        from application.shadow.cascade_orchestrator import CascadeOrchestrator
        from application.shadow.components import CascadeComponents

        cascade_processor = MagicMock()
        file_detector = MagicMock()
        file_appender = MagicMock()
        level_hierarchy = {"weekly": {"next": "monthly", "threshold": 4}}

        components = CascadeComponents(
            cascade_processor=cascade_processor,
            file_detector=file_detector,
            file_appender=file_appender,
            level_hierarchy=level_hierarchy,
        )

        # from_componentsメソッドでオーケストレーターを作成
        orchestrator = CascadeOrchestrator.from_components(components)

        assert orchestrator.cascade_processor is cascade_processor
        assert orchestrator.file_detector is file_detector
        assert orchestrator.file_appender is file_appender
        assert orchestrator.level_hierarchy == level_hierarchy
