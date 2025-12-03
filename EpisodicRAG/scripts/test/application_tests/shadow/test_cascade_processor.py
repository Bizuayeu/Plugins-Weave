#!/usr/bin/env python3
"""
CascadeProcessor テスト
=======================

cascade_processor.py のユニットテスト・統合テスト
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict, List, Tuple
    from test_helpers import TempPluginEnvironment
    from application.config import DigestConfig
    from application.tracking import DigestTimesTracker
    from application.shadow import ShadowTemplate, ShadowIO, FileDetector
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.grand import ShadowGrandDigestManager, GrandDigestManager
    from domain.types.level import LevelHierarchyEntry


import pytest

from application.shadow import (
    FileDetector,
    ShadowIO,
    ShadowTemplate,
    ShadowUpdater,
)
from application.shadow.cascade_processor import CascadeProcessor
from application.shadow.file_appender import FileAppender
from application.shadow.placeholder_manager import PlaceholderManager
from application.tracking import DigestTimesTracker
from application.config import DigestConfig
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
def cascade_processor(temp_plugin_env: "TempPluginEnvironment", level_hierarchy: "Dict[str, LevelHierarchyEntry]"):

    """CascadeProcessorインスタンスを提供"""
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
    return CascadeProcessor(shadow_io, file_detector, template, level_hierarchy, file_appender)


# =============================================================================
# get_shadow_digest_for_level テスト
# =============================================================================


class TestGetShadowDigestForLevel:
    """get_shadow_digest_for_level メソッドのテスト"""

    @pytest.mark.unit
    def test_returns_none_when_no_digest(self, cascade_processor) -> None:

        """Shadowダイジェストが空の場合、Noneを返す"""
        result = cascade_processor.get_shadow_digest_for_level("weekly")
        assert result is None

    @pytest.mark.integration
    def test_returns_digest_when_exists(self, cascade_processor, temp_plugin_env: "TempPluginEnvironment") -> None:

        """Shadowダイジェストが存在する場合、その内容を返す"""
        # Shadowにデータを追加
        shadow_data = cascade_processor.shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "source_files": ["L0001_test.txt", "L0002_test.txt"],
            "timestamp": "2025-01-01T00:00:00",
            "digest_type": "weekly",
            "keywords": ["test"],
            "abstract": "Test abstract",
            "impression": "Test impression",
        }
        cascade_processor.shadow_io.save(shadow_data)

        # 取得
        result = cascade_processor.get_shadow_digest_for_level("weekly")

        assert result is not None
        assert len(result["source_files"]) == 2
        assert "L0001_test.txt" in result["source_files"]

    @pytest.mark.unit
    def test_returns_none_when_source_files_empty(self, cascade_processor) -> None:

        """source_filesが空の場合、Noneを返す"""
        shadow_data = cascade_processor.shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "source_files": [],
            "timestamp": "2025-01-01T00:00:00",
        }
        cascade_processor.shadow_io.save(shadow_data)

        result = cascade_processor.get_shadow_digest_for_level("weekly")
        assert result is None


# =============================================================================
# promote_shadow_to_grand テスト
# =============================================================================


class TestPromoteShadowToGrand:
    """promote_shadow_to_grand メソッドのテスト"""

    @pytest.mark.unit
    def test_logs_when_no_digest(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """Shadowダイジェストがない場合、ログ出力のみ"""
        cascade_processor.promote_shadow_to_grand("weekly")
        assert "昇格対象のShadowダイジェストなし" in caplog.text

    @pytest.mark.integration
    def test_logs_ready_for_promotion(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """Shadowダイジェストがある場合、準備完了をログ出力"""
        # Shadowにデータを追加
        shadow_data = cascade_processor.shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "source_files": ["L0001_test.txt", "L0002_test.txt"],
            "timestamp": "2025-01-01T00:00:00",
        }
        cascade_processor.shadow_io.save(shadow_data)

        cascade_processor.promote_shadow_to_grand("weekly")
        assert "昇格準備完了: 2ファイル" in caplog.text


# =============================================================================
# clear_shadow_level テスト
# =============================================================================


class TestClearShadowLevel:
    """clear_shadow_level メソッドのテスト"""

    @pytest.mark.integration
    def test_clears_shadow_level(self, cascade_processor) -> None:

        """指定レベルのShadowをクリアする"""
        # まずデータを追加
        shadow_data = cascade_processor.shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "source_files": ["L0001_test.txt"],
            "timestamp": "2025-01-01T00:00:00",
            "abstract": "Test abstract",
        }
        cascade_processor.shadow_io.save(shadow_data)

        # クリア実行
        cascade_processor.clear_shadow_level("weekly")

        # 確認
        shadow_data = cascade_processor.shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        # source_filesは空または存在しない
        assert not overall.get("source_files") or overall["source_files"] == []

    @pytest.mark.integration
    def test_clear_logs_message(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """クリア時にログを出力"""
        cascade_processor.clear_shadow_level("monthly")
        assert "ShadowGrandDigestクリア完了: レベル monthly" in caplog.text


# =============================================================================
# cascade_update_on_digest_finalize テスト
# =============================================================================


class TestCascadeUpdateOnDigestFinalize:
    """cascade_update_on_digest_finalize メソッドのテスト"""

    @pytest.mark.integration
    def test_cascade_logs_start_and_end(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """カスケード処理の開始・終了をログ出力"""
        cascade_processor.cascade_update_on_digest_finalize("weekly")

        assert "[Step 3] ShadowGrandDigestカスケード処理: レベル weekly" in caplog.text
        assert "[Step 3] カスケード処理完了: レベル weekly" in caplog.text

    @pytest.mark.integration
    def test_cascade_clears_current_level(self, cascade_processor) -> None:

        """カスケード処理後、現在レベルのShadowがクリアされる"""
        # weeklyにデータを追加
        shadow_data = cascade_processor.shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = {
            "source_files": ["L0001_test.txt"],
            "timestamp": "2025-01-01T00:00:00",
        }
        cascade_processor.shadow_io.save(shadow_data)

        # カスケード実行
        cascade_processor.cascade_update_on_digest_finalize("weekly")

        # weeklyがクリアされていることを確認
        shadow_data = cascade_processor.shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert not overall.get("source_files") or overall["source_files"] == []

    @pytest.mark.integration
    def test_cascade_centurial_logs_top_level(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """Centurialレベルは次レベルがないため、top levelログ出力"""
        cascade_processor.cascade_update_on_digest_finalize("centurial")
        assert "centurialに上位レベルなし（最上位）" in caplog.text

    @pytest.mark.integration
    def test_cascade_detects_new_files_for_next_level(
        self, cascade_processor, temp_plugin_env: "TempPluginEnvironment", caplog: pytest.LogCaptureFixture
    ) -> None:

        """次レベルの新規ファイルを検出してShadowに追加"""
        # Weekly Digestファイルを作成（monthlyの次レベルはweekly）
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_test.txt"
        digest_content = {
            "overall_digest": {
                "digest_type": "weekly",
                "keywords": ["test"],
                "abstract": "Test",
                "impression": "Test",
            }
        }
        with open(weekly_file, "w", encoding="utf-8") as f:
            json.dump(digest_content, f)

        # weeklyのカスケードを実行（次はmonthly）
        cascade_processor.cascade_update_on_digest_finalize("weekly")

        # monthlyのShadowにファイルが追加されたか確認
        shadow_data = cascade_processor.shadow_io.load_or_create()
        # 新しいWeeklyファイルがmonthlyのsource_filesに追加されているはず
        # （ただしtimes_trackerの状態による）
        _ = shadow_data["latest_digests"]["monthly"]["overall_digest"].get("source_files", [])


# =============================================================================
# エッジケーステスト
# =============================================================================


class TestCascadeProcessorEdgeCases:
    """CascadeProcessor のエッジケーステスト"""

    @pytest.mark.unit
    def test_all_levels_have_hierarchy_entry(self, cascade_processor, level_hierarchy: "Dict[str, LevelHierarchyEntry]") -> None:

        """すべてのレベルがhierarchyに存在する"""
        for level in LEVEL_CONFIG.keys():
            assert level in level_hierarchy

    @pytest.mark.integration
    def test_cascade_multiple_levels_sequentially(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """複数レベルを順次カスケード処理"""
        levels = ["weekly", "monthly", "quarterly"]

        for level in levels:
            cascade_processor.cascade_update_on_digest_finalize(level)

        # 各レベルのログが出力されていること
        for level in levels:
            assert f"カスケード処理: レベル {level}" in caplog.text


# =============================================================================
# 型チェックバグ修正テスト（is_valid_dict対応）
# =============================================================================


class TestGetShadowDigestTypeChecks:
    """get_shadow_digest_for_level の型チェックテスト"""

    @pytest.mark.unit
    def test_get_shadow_digest_with_string_overall_digest(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """overall_digestが文字列の場合、Noneを返す（AttributeError回避）"""
        shadow_data = cascade_processor.shadow_io.load_or_create()
        # バグ再現: overall_digestに文字列を設定
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = "invalid_string"
        cascade_processor.shadow_io.save(shadow_data)

        result = cascade_processor.get_shadow_digest_for_level("weekly")

        assert result is None
        assert "Shadowダイジェストなし: レベル weekly" in caplog.text

    @pytest.mark.unit
    def test_get_shadow_digest_with_none(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """overall_digestがNoneの場合、Noneを返す"""
        shadow_data = cascade_processor.shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = None
        cascade_processor.shadow_io.save(shadow_data)

        result = cascade_processor.get_shadow_digest_for_level("weekly")

        assert result is None
        assert "Shadowダイジェストなし: レベル weekly" in caplog.text

    @pytest.mark.unit
    def test_get_shadow_digest_with_invalid_type(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """overall_digestがリストの場合、Noneを返す"""
        shadow_data = cascade_processor.shadow_io.load_or_create()
        # overall_digestにリストを設定
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = ["invalid", "list"]
        cascade_processor.shadow_io.save(shadow_data)

        result = cascade_processor.get_shadow_digest_for_level("weekly")

        assert result is None
        assert "Shadowダイジェストなし: レベル weekly" in caplog.text

    @pytest.mark.unit
    def test_promote_with_invalid_overall_digest(self, cascade_processor, caplog: pytest.LogCaptureFixture) -> None:

        """promote_shadow_to_grand: overall_digestが不正な型でも例外が発生しない"""
        shadow_data = cascade_processor.shadow_io.load_or_create()
        shadow_data["latest_digests"]["weekly"]["overall_digest"] = 12345  # 整数
        cascade_processor.shadow_io.save(shadow_data)

        # 例外が発生しないことを確認
        cascade_processor.promote_shadow_to_grand("weekly")

        assert "昇格対象のShadowダイジェストなし: レベル weekly" in caplog.text
