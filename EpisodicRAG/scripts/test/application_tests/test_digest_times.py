#!/usr/bin/env python3
"""
DigestTimesTracker 統合テスト
==============================

一時ディレクトリを使用したファイルI/Oテスト
pytestスタイルに移行済み
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

# Application層
from application.tracking import DigestTimesTracker


class TestDigestTimesTracker:
    """DigestTimesTracker の統合テスト"""

    @pytest.fixture
    def mock_config(self, temp_plugin_env):
        """モック設定を提供"""
        mock = MagicMock()
        mock.plugin_root = temp_plugin_env.plugin_root
        return mock

    @pytest.fixture
    def tracker(self, mock_config):
        """DigestTimesTrackerインスタンスを提供"""
        return DigestTimesTracker(mock_config)

    @pytest.mark.integration
    def test_load_or_create_empty(self, tracker):
        """空の状態からの読み込み"""
        data = tracker.load_or_create()

        # 全レベルが初期化されていることを確認
        assert "weekly" in data
        assert "centurial" in data

    @pytest.mark.integration
    def test_save_and_load(self, tracker):
        """保存と読み込み"""
        input_files = ["L00001_Test.txt", "L00002_Test.txt"]
        tracker.save("weekly", input_files)

        data = tracker.load_or_create()

        assert "timestamp" in data["weekly"]
        # last_processed is now stored as int (extracted number only)
        assert data["weekly"]["last_processed"] == 2

    @pytest.mark.unit
    def test_extract_file_numbers(self, tracker):
        """ファイル番号抽出"""
        files = ["L00001_A.txt", "L00003_B.txt"]
        numbers = tracker.extract_file_numbers("weekly", files)

        assert numbers == ["L00001", "L00003"]

    @pytest.mark.unit
    def test_extract_file_numbers_monthly(self, tracker):
        """Monthlyレベルのファイル番号抽出（Wプレフィックスは4桁維持）"""
        files = ["W0001_A.txt", "W0005_B.txt"]
        numbers = tracker.extract_file_numbers("monthly", files)

        # ソースファイル(Weekly)の形式を維持: W0001, W0005
        assert numbers == ["W0001", "W0005"]

    @pytest.mark.unit
    def test_load_or_create_initializes_all_levels(self, tracker):
        """load_or_createが全8レベルを初期化"""
        data = tracker.load_or_create()

        expected_levels = [
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

    @pytest.mark.integration
    def test_save_updates_timestamp(self, tracker):
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
