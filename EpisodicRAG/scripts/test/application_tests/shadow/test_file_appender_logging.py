#!/usr/bin/env python3
"""
file_appender DEBUGログのテスト
================================

FileAppenderのDEBUGレベルトレースが正しく出力されることを検証。

Usage:
    pytest scripts/test/application_tests/shadow/test_file_appender_logging.py -v
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

import pytest
from test_helpers import create_test_loop_file

from application.config import DigestConfig
from application.shadow import (
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
def file_appender(
    temp_plugin_env: "TempPluginEnvironment",
    level_hierarchy: "Dict[str, LevelHierarchyEntry]",
) -> FileAppender:
    """FileAppenderインスタンスを提供"""
    config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
    levels = list(LEVEL_CONFIG.keys())
    template = ShadowTemplate(levels)
    times_tracker = DigestTimesTracker(config)
    file_detector = FileDetector(config, times_tracker)
    shadow_file = temp_plugin_env.essences_path / "ShadowGrandDigest.txt"
    shadow_io = ShadowIO(shadow_file, template.get_template)
    placeholder_manager = PlaceholderManager()

    return FileAppender(
        shadow_io=shadow_io,
        file_detector=file_detector,
        template=template,
        level_hierarchy=level_hierarchy,
        placeholder_manager=placeholder_manager,
    )


@pytest.fixture
def sample_files(temp_plugin_env: "TempPluginEnvironment") -> List[Path]:
    """サンプルLoopファイルを作成"""
    files = []
    for i in range(1, 4):
        f = create_test_loop_file(temp_plugin_env.loops_path, i, f"test_{i}")
        files.append(f)
    return files


# =============================================================================
# テスト
# =============================================================================


class TestFileAppenderLogging:
    """FileAppenderのDEBUGログ出力テスト"""

    @pytest.mark.unit
    def test_logs_add_files_state(
        self,
        file_appender: FileAppender,
        sample_files: List[Path],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """add_files_to_shadow呼び出し時にSTATEログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_appender.add_files_to_shadow("weekly", sample_files)

        assert LOG_PREFIX_STATE in caplog.text
        assert "add_files_to_shadow" in caplog.text

    @pytest.mark.unit
    def test_logs_ensure_digest_initialized(
        self,
        file_appender: FileAppender,
        sample_files: List[Path],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """overall_digest初期化確認時にログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_appender.add_files_to_shadow("weekly", sample_files)

        assert LOG_PREFIX_STATE in caplog.text
        assert "_ensure_overall_digest_initialized" in caplog.text

    @pytest.mark.unit
    def test_logs_validation(
        self,
        file_appender: FileAppender,
        sample_files: List[Path],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """検証時にVALIDATEログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_appender.add_files_to_shadow("weekly", sample_files)

        assert LOG_PREFIX_VALIDATE in caplog.text

    @pytest.mark.unit
    def test_logs_files_added_count(
        self,
        file_appender: FileAppender,
        sample_files: List[Path],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """追加されたファイル数をログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_appender.add_files_to_shadow("weekly", sample_files)

        assert LOG_PREFIX_STATE in caplog.text
        assert "files_added" in caplog.text

    @pytest.mark.unit
    def test_logs_total_files_after_add(
        self,
        file_appender: FileAppender,
        sample_files: List[Path],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """追加後の合計ファイル数をログ出力"""
        with caplog.at_level(logging.DEBUG, logger="episodic_rag"):
            file_appender.add_files_to_shadow("weekly", sample_files)

        assert "total_files_after_add" in caplog.text

    @pytest.mark.unit
    def test_not_shown_at_info_level(
        self,
        file_appender: FileAppender,
        sample_files: List[Path],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """INFOレベルではDEBUGログは表示されない"""
        with caplog.at_level(logging.INFO, logger="episodic_rag"):
            file_appender.add_files_to_shadow("weekly", sample_files)

        # DEBUGログの識別子がINFOレベルでは出力されないことを確認
        assert "add_files_to_shadow" not in caplog.text
        assert "_ensure_overall_digest_initialized" not in caplog.text
