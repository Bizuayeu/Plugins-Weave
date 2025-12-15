#!/usr/bin/env python3
"""
CascadeOrchestrator テスト
===========================

Orchestrator Pattern 実装のテスト。
- ステップ実行と結果集約
- 各ステップの状態管理
"""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict, List, Tuple

    from test_helpers import TempPluginEnvironment

    from application.config import DigestConfig
    from application.grand import GrandDigestManager, ShadowGrandDigestManager
    from application.shadow import FileDetector, ShadowIO, ShadowTemplate
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.tracking import DigestTimesTracker
    from domain.types.level import LevelHierarchyEntry


import pytest

from application.config import DigestConfig
from application.shadow import (
    CascadeOrchestrator,
    CascadeProcessor,
    CascadeResult,
    CascadeStepResult,
    CascadeStepStatus,
    FileDetector,
    ShadowIO,
    ShadowTemplate,
)
from application.shadow.file_appender import FileAppender
from application.shadow.placeholder_manager import PlaceholderManager
from application.tracking import DigestTimesTracker
from domain.constants import LEVEL_CONFIG

# slow マーカーを適用（ファイル全体）
pytestmark = pytest.mark.slow


# =============================================================================
# フィクスチャ
# =============================================================================


@pytest.fixture
def level_hierarchy():
    """レベル階層情報"""
    return {
        level: {"source": cfg["source"], "next": cfg["next"]} for level, cfg in LEVEL_CONFIG.items()
    }


@pytest.fixture
def cascade_components(
    temp_plugin_env: "TempPluginEnvironment", level_hierarchy: "Dict[str, LevelHierarchyEntry]"
):
    """カスケード処理に必要なコンポーネント群"""
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
    cascade_processor = CascadeProcessor(
        shadow_io, file_detector, template, level_hierarchy, file_appender
    )

    return {
        "config": config,
        "template": template,
        "file_detector": file_detector,
        "shadow_io": shadow_io,
        "file_appender": file_appender,
        "cascade_processor": cascade_processor,
        "level_hierarchy": level_hierarchy,
    }


@pytest.fixture
def cascade_orchestrator(cascade_components, level_hierarchy: "Dict[str, LevelHierarchyEntry]"):
    """CascadeOrchestratorインスタンスを提供"""
    return CascadeOrchestrator(
        cascade_processor=cascade_components["cascade_processor"],
        file_detector=cascade_components["file_detector"],
        file_appender=cascade_components["file_appender"],
        level_hierarchy=level_hierarchy,
    )


# =============================================================================
# CascadeStepResult Tests
# =============================================================================


class TestCascadeStepResult:
    """CascadeStepResult dataclass tests"""

    @pytest.mark.unit
    def test_create_step_result(self) -> None:
        """Create step result with all fields"""
        result = CascadeStepResult(
            step_name="promote",
            status=CascadeStepStatus.SUCCESS,
            message="Test message",
            files_processed=5,
            details={"key": "value"},
        )

        assert result.step_name == "promote"
        assert result.status == CascadeStepStatus.SUCCESS
        assert result.message == "Test message"
        assert result.files_processed == 5
        assert result.details == {"key": "value"}

    @pytest.mark.unit
    def test_step_result_defaults(self) -> None:
        """Step result has sensible defaults"""
        result = CascadeStepResult(
            step_name="test",
            status=CascadeStepStatus.SKIPPED,
            message="Skipped",
        )

        assert result.files_processed == 0
        assert result.details == {}


# =============================================================================
# CascadeResult Tests
# =============================================================================


class TestCascadeResult:
    """CascadeResult dataclass tests"""

    @pytest.mark.unit
    def test_create_cascade_result(self) -> None:
        """Create cascade result"""
        steps = [
            CascadeStepResult("promote", CascadeStepStatus.SUCCESS, "OK", 3),
            CascadeStepResult("detect", CascadeStepStatus.SUCCESS, "OK", 5),
        ]
        result = CascadeResult(
            level="weekly",
            steps=steps,
            success=True,
            next_level="monthly",
        )

        assert result.level == "weekly"
        assert len(result.steps) == 2
        assert result.success is True
        assert result.next_level == "monthly"

    @pytest.mark.unit
    def test_total_files_processed(self) -> None:
        """total_files_processed sums all step counts"""
        steps = [
            CascadeStepResult("promote", CascadeStepStatus.SUCCESS, "OK", 3),
            CascadeStepResult("detect", CascadeStepStatus.SUCCESS, "OK", 5),
            CascadeStepResult("add", CascadeStepStatus.SUCCESS, "OK", 5),
            CascadeStepResult("clear", CascadeStepStatus.SUCCESS, "OK", 0),
        ]
        result = CascadeResult(level="weekly", steps=steps, success=True)

        # Should sum: 3 + 5 + 5 + 0 = 13
        assert result.total_files_processed == 13

    @pytest.mark.unit
    def test_step_summary(self) -> None:
        """step_summary returns status mapping"""
        steps = [
            CascadeStepResult("promote", CascadeStepStatus.SUCCESS, "OK"),
            CascadeStepResult("detect", CascadeStepStatus.NO_DATA, "No files"),
            CascadeStepResult("add", CascadeStepStatus.SKIPPED, "Skip"),
            CascadeStepResult("clear", CascadeStepStatus.SUCCESS, "OK"),
        ]
        result = CascadeResult(level="weekly", steps=steps, success=True)

        summary = result.step_summary
        assert summary["promote"] == CascadeStepStatus.SUCCESS
        assert summary["detect"] == CascadeStepStatus.NO_DATA
        assert summary["add"] == CascadeStepStatus.SKIPPED
        assert summary["clear"] == CascadeStepStatus.SUCCESS


# =============================================================================
# CascadeOrchestrator Basic Tests
# =============================================================================


class TestCascadeOrchestratorInit:
    """CascadeOrchestrator initialization tests"""

    @pytest.mark.unit
    def test_init_with_components(
        self, cascade_components, level_hierarchy: "Dict[str, LevelHierarchyEntry]"
    ) -> None:
        """Initialize with all required components"""
        orchestrator = CascadeOrchestrator(
            cascade_processor=cascade_components["cascade_processor"],
            file_detector=cascade_components["file_detector"],
            file_appender=cascade_components["file_appender"],
            level_hierarchy=level_hierarchy,
        )

        assert orchestrator.cascade_processor is not None
        assert orchestrator.file_detector is not None
        assert orchestrator.file_appender is not None
        assert orchestrator.level_hierarchy == level_hierarchy


# =============================================================================
# CascadeOrchestrator Execute Tests
# =============================================================================


class TestCascadeOrchestratorExecute:
    """CascadeOrchestrator.execute_cascade tests"""

    @pytest.mark.integration
    def test_execute_returns_cascade_result(self, cascade_orchestrator) -> None:
        """execute_cascade returns CascadeResult"""
        result = cascade_orchestrator.execute_cascade("weekly")

        assert isinstance(result, CascadeResult)
        assert result.level == "weekly"
        assert result.success is True

    @pytest.mark.integration
    def test_execute_has_four_steps(self, cascade_orchestrator) -> None:
        """execute_cascade runs all four steps"""
        result = cascade_orchestrator.execute_cascade("weekly")

        assert len(result.steps) == 4
        step_names = [step.step_name for step in result.steps]
        assert "promote" in step_names
        assert "detect" in step_names
        assert "add" in step_names
        assert "clear" in step_names

    @pytest.mark.integration
    def test_execute_identifies_next_level(self, cascade_orchestrator) -> None:
        """execute_cascade identifies next level"""
        result = cascade_orchestrator.execute_cascade("weekly")

        # weekly's next level is monthly
        assert result.next_level == "monthly"

    @pytest.mark.integration
    def test_execute_top_level_has_no_next(self, cascade_orchestrator) -> None:
        """Top level (centurial) has no next level"""
        result = cascade_orchestrator.execute_cascade("centurial")

        assert result.next_level is None
        # detect and add should be skipped
        summary = result.step_summary
        assert summary["detect"] == CascadeStepStatus.SKIPPED


class TestCascadeOrchestratorSteps:
    """Individual step execution tests"""

    @pytest.mark.integration
    def test_promote_step_no_data(self, cascade_orchestrator) -> None:
        """Promote step returns NO_DATA when shadow is empty"""
        result = cascade_orchestrator.execute_cascade("weekly")

        promote_step = next(s for s in result.steps if s.step_name == "promote")
        assert promote_step.status == CascadeStepStatus.NO_DATA

    @pytest.mark.integration
    def test_promote_step_success_with_data(self, cascade_orchestrator, cascade_components) -> None:
        """Promote step returns SUCCESS when shadow has data"""
        # Add data to shadow
        shadow_io = cascade_components["shadow_io"]
        shadow_data = shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "source_files": ["L0001_test.txt", "L0002_test.txt"],
            "timestamp": "2025-01-01T00:00:00",
            "digest_type": "weekly",
            "keywords": ["test"],
            "abstract": "Test abstract",
            "impression": "Test impression",
        }
        shadow_io.save(shadow_data)

        result = cascade_orchestrator.execute_cascade("weekly")

        promote_step = next(s for s in result.steps if s.step_name == "promote")
        assert promote_step.status == CascadeStepStatus.SUCCESS
        assert promote_step.files_processed == 2

    @pytest.mark.integration
    def test_detect_step_no_files(self, cascade_orchestrator) -> None:
        """Detect step returns NO_DATA when no new files"""
        result = cascade_orchestrator.execute_cascade("weekly")

        detect_step = next(s for s in result.steps if s.step_name == "detect")
        assert detect_step.status == CascadeStepStatus.NO_DATA

    @pytest.mark.integration
    def test_clear_step_always_succeeds(self, cascade_orchestrator) -> None:
        """Clear step always returns SUCCESS"""
        result = cascade_orchestrator.execute_cascade("weekly")

        clear_step = next(s for s in result.steps if s.step_name == "clear")
        assert clear_step.status == CascadeStepStatus.SUCCESS


# =============================================================================
# Import Tests
# =============================================================================


class TestCascadeOrchestratorImports:
    """CascadeOrchestrator import path tests"""

    @pytest.mark.unit
    def test_import_from_package(self) -> None:
        """Import from application.shadow package"""
        from application.shadow import (
            CascadeOrchestrator,
            CascadeResult,
            CascadeStepResult,
            CascadeStepStatus,
        )

        assert CascadeOrchestrator is not None
        assert CascadeResult is not None
        assert CascadeStepResult is not None
        assert CascadeStepStatus is not None

    @pytest.mark.unit
    def test_import_from_module(self) -> None:
        """Import from application.shadow.cascade_orchestrator module"""
        from application.shadow.cascade_orchestrator import (
            CascadeOrchestrator,
            CascadeResult,
            CascadeStepResult,
            CascadeStepStatus,
        )

        assert CascadeOrchestrator is not None
        assert CascadeResult is not None
        assert CascadeStepResult is not None
        assert CascadeStepStatus is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
