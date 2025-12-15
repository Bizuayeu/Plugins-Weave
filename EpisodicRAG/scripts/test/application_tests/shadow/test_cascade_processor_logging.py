#!/usr/bin/env python3
"""
cascade_processor DEBUGログのテスト
====================================

CascadeProcessorのDEBUGレベルトレースが正しく出力されることを検証。

Usage:
    pytest scripts/test/application_tests/shadow/test_cascade_processor_logging.py -v
"""

import logging
from typing import TYPE_CHECKING, Dict

import pytest

from application.config import DigestConfig
from application.shadow import (
    CascadeProcessor,
    FileDetector,
    ShadowIO,
    ShadowTemplate,
)
from application.shadow.file_appender import FileAppender
from application.shadow.placeholder_manager import PlaceholderManager
from application.tracking import DigestTimesTracker
from domain.constants import (
    LEVEL_CONFIG,
    LOG_PREFIX_DECISION,
    LOG_PREFIX_STATE,
    LOG_PREFIX_VALIDATE,
)

if TYPE_CHECKING:
    from test_helpers import TempPluginEnvironment

    from domain.types.level import LevelHierarchyEntry


# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def level_hierarchy() -> "Dict[str, LevelHierarchyEntry]":
    """レベル階層情報"""
    return {
        level: {"source": cfg["source"], "next": cfg["next"]} for level, cfg in LEVEL_CONFIG.items()
    }


@pytest.fixture
def cascade_processor(
    temp_plugin_env: "TempPluginEnvironment",
    level_hierarchy: "Dict[str, LevelHierarchyEntry]",
) -> CascadeProcessor:
    """CascadeProcessorインスタンスを提供"""
    config = DigestConfig()
    levels = list(LEVEL_CONFIG.keys())
    template = ShadowTemplate(levels)
    times_tracker = DigestTimesTracker(config)
    file_detector = FileDetector(config, times_tracker)
    shadow_file = temp_plugin_env.essences_path / "ShadowGrandDigest.txt"
    shadow_io = ShadowIO(shadow_file, template.get_template)
    placeholder_manager = PlaceholderManager()
    file_appender = FileAppender(
        shadow_io, file_detector, template, level_hierarchy, placeholder_manager
    )

    return CascadeProcessor(
        shadow_io=shadow_io,
        file_detector=file_detector,
        template=template,
        level_hierarchy=level_hierarchy,
        file_appender=file_appender,
    )


# =============================================================================
# テスト
# =============================================================================


class TestCascadeProcessorLogging:
    """CascadeProcessorのDEBUGログ出力テスト"""

    @pytest.mark.unit
    def test_logs_get_shadow_digest_state(
        self,
        cascade_processor: CascadeProcessor,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """get_shadow_digest_for_level呼び出し時にSTATEログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_processor.get_shadow_digest_for_level("weekly")

        assert LOG_PREFIX_STATE in caplog.text
        assert "get_shadow_digest_for_level" in caplog.text

    @pytest.mark.unit
    def test_logs_validation_for_overall_digest(
        self,
        cascade_processor: CascadeProcessor,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """overall_digestの検証時にVALIDATEログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_processor.get_shadow_digest_for_level("weekly")

        assert LOG_PREFIX_VALIDATE in caplog.text
        assert "overall_digest" in caplog.text

    @pytest.mark.unit
    def test_logs_cascade_update_state(
        self,
        cascade_processor: CascadeProcessor,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """cascade_update開始時にSTATEログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_processor.cascade_update_on_digest_finalize("weekly")

        assert LOG_PREFIX_STATE in caplog.text
        assert "cascade_update" in caplog.text

    @pytest.mark.unit
    def test_logs_next_level_decision(
        self,
        cascade_processor: CascadeProcessor,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """次レベル決定時にDECISIONログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_processor.cascade_update_on_digest_finalize("weekly")

        assert LOG_PREFIX_DECISION in caplog.text
        assert "next_level" in caplog.text

    @pytest.mark.unit
    def test_not_shown_at_info_level(
        self,
        cascade_processor: CascadeProcessor,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """INFOレベルではDEBUGログ（cascade_update等）は表示されない"""
        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            cascade_processor.cascade_update_on_digest_finalize("weekly")

        # DEBUGログのメッセージがINFOレベルでは出力されないことを確認
        assert "cascade_update" not in caplog.text
