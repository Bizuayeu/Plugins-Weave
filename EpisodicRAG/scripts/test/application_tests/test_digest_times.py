#!/usr/bin/env python3
"""
DigestTimesTracker 統合テスト
==============================

一時ディレクトリを使用したファイルI/Oテスト
pytestスタイルに移行済み
"""

from datetime import datetime
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

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

# Application層
from application.tracking import DigestTimesTracker


class TestDigestTimesTracker:
    """DigestTimesTracker の統合テスト"""

    @pytest.fixture
    def mock_config(self, temp_plugin_env: "TempPluginEnvironment"):
        """モック設定を提供"""
        mock = MagicMock()
        mock.plugin_root = temp_plugin_env.plugin_root
        return mock

    @pytest.fixture
    def tracker(self, mock_config):
        """DigestTimesTrackerインスタンスを提供"""
        return DigestTimesTracker(mock_config)

    @pytest.mark.integration
    def test_load_or_create_empty(self, tracker) -> None:
        """空の状態からの読み込み"""
        data = tracker.load_or_create()

        # 全レベルが初期化されていることを確認
        assert "weekly" in data
        assert "centurial" in data

    @pytest.mark.integration
    def test_save_and_load(self, tracker) -> None:
        """保存と読み込み"""
        input_files = ["L00001_Test.txt", "L00002_Test.txt"]
        tracker.save("weekly", input_files)

        data = tracker.load_or_create()

        assert "timestamp" in data["weekly"]
        # last_processed is now stored as int (extracted number only)
        assert data["weekly"]["last_processed"] == 2

    @pytest.mark.unit
    def test_extract_file_numbers(self, tracker) -> None:
        """ファイル番号抽出"""
        files = ["L00001_A.txt", "L00003_B.txt"]
        numbers = tracker.extract_file_numbers("weekly", files)

        assert numbers == ["L00001", "L00003"]

    @pytest.mark.unit
    def test_extract_file_numbers_monthly(self, tracker) -> None:
        """Monthlyレベルのファイル番号抽出（Wプレフィックスは4桁維持）"""
        files = ["W0001_A.txt", "W0005_B.txt"]
        numbers = tracker.extract_file_numbers("monthly", files)

        # ソースファイル(Weekly)の形式を維持: W0001, W0005
        assert numbers == ["W0001", "W0005"]

    @pytest.mark.unit
    def test_load_or_create_initializes_all_levels(self, tracker) -> None:
        """load_or_createが全9レベルを初期化（loop + 8ダイジェストレベル）"""
        data = tracker.load_or_create()

        expected_levels = [
            "loop",
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            "triennial",
            "decadal",
            "multi_decadal",
            "centurial",
        ]
        for level in expected_levels:
            assert level in data

    @pytest.mark.unit
    def test_load_or_create_includes_loop_level(self, tracker) -> None:
        """load_or_createがloopレベルを含む"""
        data = tracker.load_or_create()

        assert "loop" in data
        assert data["loop"]["last_processed"] is None

    @pytest.mark.integration
    def test_save_loop_level(self, tracker) -> None:
        """loopレベルの保存と読み込み"""
        input_files = ["L00255.txt", "L00256.txt", "L00257.txt"]
        tracker.save("loop", input_files)

        data = tracker.load_or_create()

        assert "timestamp" in data["loop"]
        assert data["loop"]["last_processed"] == 257

    @pytest.mark.integration
    def test_save_updates_timestamp(self, tracker) -> None:
        """saveがtimestampを更新"""
        input_files = ["L00001_Test.txt"]
        tracker.save("weekly", input_files)

        data = tracker.load_or_create()

        timestamp_str = data["weekly"]["timestamp"]
        assert timestamp_str is not None
        assert timestamp_str != ""
        # ISO形式であることを検証（無効な形式は例外を発生）
        timestamp = datetime.fromisoformat(timestamp_str)
        assert timestamp is not None

    # ====== update_direct() テスト ======

    @pytest.mark.integration
    def test_update_direct_sets_last_processed(self, tracker) -> None:
        """update_direct()で直接last_processedを設定"""
        tracker.update_direct("loop", 259)

        data = tracker.load_or_create()

        assert data["loop"]["last_processed"] == 259
        assert data["loop"]["timestamp"]  # 更新されている

    @pytest.mark.integration
    def test_update_direct_updates_timestamp(self, tracker) -> None:
        """update_direct()がtimestampを更新"""
        tracker.update_direct("weekly", 51)

        data = tracker.load_or_create()

        timestamp_str = data["weekly"]["timestamp"]
        assert timestamp_str is not None
        assert timestamp_str != ""
        # ISO形式であることを検証
        timestamp = datetime.fromisoformat(timestamp_str)
        assert timestamp is not None

    @pytest.mark.integration
    def test_update_direct_preserves_other_levels(self, tracker) -> None:
        """update_direct()が他のレベルを保持"""
        # まずweeklyを設定
        tracker.save("weekly", ["W0040_Test.txt"])

        # loopをupdate_directで更新
        tracker.update_direct("loop", 259)

        data = tracker.load_or_create()

        # loopは更新されている
        assert data["loop"]["last_processed"] == 259
        # weeklyは保持されている
        assert data["weekly"]["last_processed"] == 40

    # ====== 共通ロジックのリファクタリングテスト ======

    @pytest.mark.integration
    def test_save_uses_internal_update(self, tracker) -> None:
        """save()内部でupdate_directと同じ保存ロジックを使用"""
        # save()を使用してweeklyを更新
        tracker.save("weekly", ["W0040_test.txt", "W0041_test.txt"])

        data = tracker.load_or_create()

        # 最後のファイル番号が保存されている
        assert data["weekly"]["last_processed"] == 41

    @pytest.mark.integration
    def test_save_and_update_direct_produce_consistent_structure(self, tracker) -> None:
        """save()とupdate_direct()が一貫した構造を生成"""
        # save()でweeklyを更新
        tracker.save("weekly", ["W0040_test.txt"])
        weekly_data = tracker.load_or_create()["weekly"]

        # update_direct()でmonthlyを更新
        tracker.update_direct("monthly", 10)
        monthly_data = tracker.load_or_create()["monthly"]

        # 両方とも同じキーを持つ
        assert set(weekly_data.keys()) == set(monthly_data.keys())
        assert "timestamp" in weekly_data
        assert "last_processed" in weekly_data
