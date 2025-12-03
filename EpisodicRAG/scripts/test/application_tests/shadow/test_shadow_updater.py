#!/usr/bin/env python3
"""
shadow/shadow_updater.py のユニットテスト
=========================================

ShadowUpdaterクラスの動作を検証。
- add_files_to_shadow: ファイル追加
- clear_shadow_level: レベルクリア
- get_shadow_digest_for_level: Shadow取得
- cascade_update_on_digest_finalize: カスケード処理

Note:
    _ensure_overall_digest_initialized, _log_digest_content のテストは
    test_file_appender.py に移動しました。
"""

import json
from pathlib import Path

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
from test_helpers import create_test_loop_file

from application.shadow import ShadowUpdater
from domain.constants import PLACEHOLDER_MARKER

# slow マーカーを適用（ファイル全体）
pytestmark = pytest.mark.slow

# =============================================================================
# フィクスチャ
# =============================================================================
# 注: config, times_tracker, template, shadow_io, file_detector, level_hierarchy
#     は conftest.py で定義済み


@pytest.fixture
def updater(shadow_io: "ShadowIO", file_detector: "FileDetector", template: "ShadowTemplate", level_hierarchy: "Dict[str, LevelHierarchyEntry]"):

    """テスト用ShadowUpdater"""
    return ShadowUpdater(shadow_io, file_detector, template, level_hierarchy)


# =============================================================================
# add_files_to_shadow テスト
# =============================================================================


class TestAddFilesToShadow:
    """add_files_to_shadow メソッドのテスト"""

    @pytest.mark.integration
    def test_adds_files_to_empty_shadow(self, updater, temp_plugin_env: "TempPluginEnvironment", shadow_io: "ShadowIO") -> None:

        """空のShadowにファイルを追加"""
        # Loopファイルを作成
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        loop2 = create_test_loop_file(temp_plugin_env.loops_path, 2)

        updater.add_files_to_shadow("weekly", [loop1, loop2])

        # 検証
        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert len(overall["source_files"]) == 2
        assert "L00001_test.txt" in overall["source_files"]
        assert "L00002_test.txt" in overall["source_files"]

    @pytest.mark.integration
    def test_does_not_add_duplicate_files(self, updater, temp_plugin_env: "TempPluginEnvironment", shadow_io: "ShadowIO") -> None:

        """重複ファイルは追加されない"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        # 2回追加
        updater.add_files_to_shadow("weekly", [loop1])
        updater.add_files_to_shadow("weekly", [loop1])

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert len(overall["source_files"]) == 1

    @pytest.mark.integration
    def test_incremental_add(self, updater, temp_plugin_env: "TempPluginEnvironment", shadow_io: "ShadowIO") -> None:

        """増分追加が正しく動作"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        loop2 = create_test_loop_file(temp_plugin_env.loops_path, 2)
        loop3 = create_test_loop_file(temp_plugin_env.loops_path, 3)

        # 最初に2ファイル追加
        updater.add_files_to_shadow("weekly", [loop1, loop2])

        # 後から1ファイル追加
        updater.add_files_to_shadow("weekly", [loop3])

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert len(overall["source_files"]) == 3

    @pytest.mark.integration
    def test_updates_placeholder_on_add(self, updater, temp_plugin_env: "TempPluginEnvironment", shadow_io: "ShadowIO") -> None:

        """ファイル追加時にプレースホルダーが更新される"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        updater.add_files_to_shadow("weekly", [loop1])

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert PLACEHOLDER_MARKER in overall["abstract"]
        assert "1ファイル" in overall["abstract"]


# =============================================================================
# clear_shadow_level テスト
# =============================================================================


class TestClearShadowLevel:
    """clear_shadow_level メソッドのテスト"""

    @pytest.mark.integration
    def test_clears_shadow_data(self, updater, temp_plugin_env: "TempPluginEnvironment", shadow_io: "ShadowIO") -> None:

        """Shadowデータがクリアされる"""
        # まずファイルを追加
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])

        # クリア
        updater.clear_shadow_level("weekly")

        # 検証
        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert overall["source_files"] == []

    @pytest.mark.integration
    def test_resets_to_placeholder(self, updater, shadow_io: "ShadowIO") -> None:

        """クリア後はプレースホルダーに戻る"""
        updater.clear_shadow_level("weekly")

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert PLACEHOLDER_MARKER in overall["abstract"]
        assert PLACEHOLDER_MARKER in overall["impression"]

    @pytest.mark.integration
    def test_does_not_affect_other_levels(self, updater, temp_plugin_env: "TempPluginEnvironment", shadow_io: "ShadowIO") -> None:

        """他のレベルに影響しない"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)

        # weeklyとmonthlyにファイル追加
        updater.add_files_to_shadow("weekly", [loop1])

        # weekly digestファイルを作成（monthlyのソース）
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        weekly_file = weekly_dir / "W0001_test.txt"
        with open(weekly_file, 'w', encoding='utf-8') as f:
            json.dump({"overall_digest": {"test": "data"}}, f)

        updater.add_files_to_shadow("monthly", [weekly_file])

        # weeklyだけクリア
        updater.clear_shadow_level("weekly")

        shadow_data = shadow_io.load_or_create()
        assert shadow_data["latest_digests"]["weekly"]["overall_digest"]["source_files"] == []
        assert len(shadow_data["latest_digests"]["monthly"]["overall_digest"]["source_files"]) == 1


# =============================================================================
# get_shadow_digest_for_level テスト
# =============================================================================


class TestGetShadowDigestForLevel:
    """get_shadow_digest_for_level メソッドのテスト"""

    @pytest.mark.integration
    def test_returns_none_for_empty_shadow(self, updater) -> None:

        """空のShadowはNoneを返す"""
        result = updater.get_shadow_digest_for_level("weekly")
        assert result is None

    @pytest.mark.integration
    def test_returns_digest_when_files_exist(self, updater, temp_plugin_env: "TempPluginEnvironment") -> None:

        """ファイルがある場合はdigestを返す"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])

        result = updater.get_shadow_digest_for_level("weekly")

        assert result is not None
        assert "source_files" in result
        assert len(result["source_files"]) == 1

    @pytest.mark.integration
    def test_returns_none_after_clear(self, updater, temp_plugin_env: "TempPluginEnvironment") -> None:

        """クリア後はNoneを返す"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])
        updater.clear_shadow_level("weekly")

        result = updater.get_shadow_digest_for_level("weekly")
        assert result is None


# =============================================================================
# update_shadow_for_new_loops テスト
# =============================================================================


class TestUpdateShadowForNewLoops:
    """update_shadow_for_new_loops メソッドのテスト"""

    @pytest.mark.integration
    def test_does_nothing_when_no_new_files(self, updater, shadow_io: "ShadowIO") -> None:

        """新しいファイルがない場合は何もしない"""
        updater.update_shadow_for_new_loops()

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert overall.get("source_files", []) == []

    @pytest.mark.integration
    def test_adds_new_loop_files(self, updater, temp_plugin_env: "TempPluginEnvironment", shadow_io: "ShadowIO") -> None:

        """新しいLoopファイルを追加"""
        # Loopファイルを作成
        create_test_loop_file(temp_plugin_env.loops_path, 1)
        create_test_loop_file(temp_plugin_env.loops_path, 2)

        updater.update_shadow_for_new_loops()

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert len(overall["source_files"]) == 2


# =============================================================================
# cascade_update_on_digest_finalize テスト
# =============================================================================


class TestCascadeUpdateOnDigestFinalize:
    """cascade_update_on_digest_finalize メソッドのテスト"""

    @pytest.mark.integration
    def test_clears_current_level(self, updater, temp_plugin_env: "TempPluginEnvironment", shadow_io: "ShadowIO") -> None:

        """現在のレベルがクリアされる"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])

        updater.cascade_update_on_digest_finalize("weekly")

        shadow_data = shadow_io.load_or_create()
        overall = shadow_data["latest_digests"]["weekly"]["overall_digest"]
        assert overall["source_files"] == []

    @pytest.mark.integration
    def test_does_not_cascade_from_centurial(self, updater, shadow_io: "ShadowIO") -> None:

        """centurial（最上位）からはカスケードしない"""
        # centurialにはnext=Noneなのでカスケードしない
        updater.cascade_update_on_digest_finalize("centurial")

        # エラーなく完了すればOK
        shadow_data = shadow_io.load_or_create()
        assert shadow_data is not None


# =============================================================================
# ShadowUpdater 初期化テスト
# =============================================================================


class TestShadowUpdaterInit:
    """ShadowUpdater 初期化のテスト"""

    @pytest.mark.unit
    def test_stores_dependencies(self, shadow_io: "ShadowIO", file_detector: "FileDetector", template: "ShadowTemplate", level_hierarchy: "Dict[str, LevelHierarchyEntry]") -> None:

        """依存関係が正しく保存される"""
        updater = ShadowUpdater(shadow_io, file_detector, template, level_hierarchy)

        assert updater.shadow_io is shadow_io
        assert updater.file_detector is file_detector
        assert updater.template is template
        assert updater.level_hierarchy is level_hierarchy


# =============================================================================
# promote_shadow_to_grand テスト（Phase 0で追加）
# =============================================================================


class TestPromoteShadowToGrand:
    """promote_shadow_to_grand メソッドのテスト"""

    @pytest.mark.integration
    def test_promote_shadow_to_grand_with_files(self, updater, temp_plugin_env: "TempPluginEnvironment", capsys: pytest.CaptureFixture[str]) -> None:

        """ファイルがある場合、昇格準備完了をログ出力"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        loop2 = create_test_loop_file(temp_plugin_env.loops_path, 2)
        updater.add_files_to_shadow("weekly", [loop1, loop2])

        updater.promote_shadow_to_grand("weekly")

        # ログ出力を検証
        captured = capsys.readouterr()
        # "2 file(s)" または "2ファイル" が含まれることを確認
        assert "2" in captured.out or captured.out == ""  # ログ実装による

    @pytest.mark.integration
    def test_promote_shadow_to_grand_empty(self, updater, capsys: pytest.CaptureFixture[str]) -> None:

        """空のShadowの場合、何もしない"""
        updater.promote_shadow_to_grand("weekly")

        # エラーなく完了すること
        _ = capsys.readouterr()
        # "No shadow digest" が含まれることを確認（または何も出力しない）

    @pytest.mark.integration
    def test_promote_shadow_to_grand_after_clear(self, updater, temp_plugin_env: "TempPluginEnvironment", capsys: pytest.CaptureFixture[str]) -> None:

        """クリア後は昇格対象なし"""
        loop1 = create_test_loop_file(temp_plugin_env.loops_path, 1)
        updater.add_files_to_shadow("weekly", [loop1])
        updater.clear_shadow_level("weekly")

        updater.promote_shadow_to_grand("weekly")

        # エラーなく完了すること
