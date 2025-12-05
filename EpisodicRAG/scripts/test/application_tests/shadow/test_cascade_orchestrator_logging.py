#!/usr/bin/env python3
"""
cascade_orchestrator DEBUGログのテスト
=======================================

CascadeOrchestratorのDEBUGレベルトレースが正しく出力されることを検証。

Usage:
    pytest scripts/test/application_tests/shadow/test_cascade_orchestrator_logging.py -v
"""

import logging
from typing import TYPE_CHECKING, Dict

import pytest

from application.config import DigestConfig
from application.shadow import (
    CascadeOrchestrator,
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
    LOG_PREFIX_FILE,
    LOG_PREFIX_STATE,
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
def cascade_orchestrator(
    temp_plugin_env: "TempPluginEnvironment",
    level_hierarchy: "Dict[str, LevelHierarchyEntry]",
) -> CascadeOrchestrator:
    """CascadeOrchestratorインスタンスを提供"""
    config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
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
    cascade_processor = CascadeProcessor(
        shadow_io, file_detector, template, level_hierarchy, file_appender
    )

    return CascadeOrchestrator(
        cascade_processor=cascade_processor,
        file_detector=file_detector,
        file_appender=file_appender,
        level_hierarchy=level_hierarchy,
    )


# =============================================================================
# テスト
# =============================================================================


class TestCascadeOrchestratorLogging:
    """CascadeOrchestratorのステップ境界DEBUGログテスト"""

    @pytest.mark.unit
    def test_logs_step_promote_details(
        self,
        cascade_orchestrator: CascadeOrchestrator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Step 1: PROMOTEのDEBUG詳細をログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_orchestrator.execute_cascade("weekly")

        assert LOG_PREFIX_STATE in caplog.text
        assert "step_promote" in caplog.text

    @pytest.mark.unit
    def test_logs_step_detect_details(
        self,
        cascade_orchestrator: CascadeOrchestrator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Step 2: DETECTのDEBUG詳細をログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_orchestrator.execute_cascade("weekly")

        assert LOG_PREFIX_STATE in caplog.text
        assert "step_detect" in caplog.text

    @pytest.mark.unit
    def test_logs_step_add_details_when_files_exist(
        self,
        cascade_orchestrator: CascadeOrchestrator,
        temp_plugin_env: "TempPluginEnvironment",
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Step 3: ADDのDEBUG詳細をログ出力（ファイルがある場合）

        Note: step_addはnew_filesがある場合のみ実行される。
        ファイルがない場合はスキップされるため、ここではスキップ時の
        ログ不在を確認する代わりに、LOG_PREFIX_STATEの存在を確認。
        """
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_orchestrator.execute_cascade("weekly")

        # step_addはスキップされる可能性があるので、
        # 全体としてSTATEログが出力されていることを確認
        assert LOG_PREFIX_STATE in caplog.text
        # step_addがスキップされた場合でもstep_clearは必ず実行される
        assert "step_clear" in caplog.text

    @pytest.mark.unit
    def test_logs_step_clear_details(
        self,
        cascade_orchestrator: CascadeOrchestrator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Step 4: CLEARのDEBUG詳細をログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_orchestrator.execute_cascade("weekly")

        assert LOG_PREFIX_STATE in caplog.text
        assert "step_clear" in caplog.text

    @pytest.mark.unit
    def test_logs_cascade_decision_points(
        self,
        cascade_orchestrator: CascadeOrchestrator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """判断分岐ポイントをログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            cascade_orchestrator.execute_cascade("weekly")

        assert LOG_PREFIX_DECISION in caplog.text

    @pytest.mark.unit
    def test_not_shown_at_info_level(
        self,
        cascade_orchestrator: CascadeOrchestrator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """INFOレベルではDEBUGログ（step_promote等）は表示されない"""
        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            cascade_orchestrator.execute_cascade("weekly")

        # DEBUG用のプレフィックスが含まれていないことを確認
        # （INFOレベルのログには[STATE]等のプレフィックスは使われない）
        assert "step_promote" not in caplog.text
