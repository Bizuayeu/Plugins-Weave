#!/usr/bin/env python3
"""
shadow/file_detector.py のユニットテスト
========================================

FileDetectorクラスの動作を検証。
- get_source_path: ソースディレクトリ取得
- get_max_file_number: 最大処理済みファイル番号取得
- find_new_files: 新規ファイル検出
"""
import json
import pytest
from pathlib import Path

# Application層
from application.shadow import FileDetector
from application.tracking import DigestTimesTracker

# Domain層
from domain.constants import LEVEL_CONFIG

# 設定
from config import DigestConfig
from test_helpers import create_test_loop_file


# =============================================================================
# FileDetector.get_source_path テスト
# =============================================================================

class TestFileDetectorGetSourcePath:
    """get_source_path メソッドのテスト"""

    @pytest.fixture
    def detector(self, temp_plugin_env):
        """テスト用FileDetectorインスタンス"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        times_tracker = DigestTimesTracker(config)
        return FileDetector(config, times_tracker)

    @pytest.mark.unit
    @pytest.mark.parametrize("level,expected_subdir", [
        ("monthly", "1_Weekly"),
        ("quarterly", "2_Monthly"),
        ("annual", "3_Quarterly"),
        ("triennial", "4_Annual"),
        ("decadal", "5_Triennial"),
        ("multi_decadal", "6_Decadal"),
        ("centurial", "7_Multi-decadal"),
    ])
    def test_levels_return_correct_source_dir(self, detector, temp_plugin_env, level, expected_subdir):
        """各レベルが正しいソースディレクトリを返す"""
        result = detector.get_source_path(level)
        expected = temp_plugin_env.digests_path / expected_subdir
        assert result == expected

    @pytest.mark.unit
    def test_weekly_returns_loops_path(self, detector, temp_plugin_env):
        """weeklyのソースはloops_path"""
        result = detector.get_source_path("weekly")
        assert result == temp_plugin_env.loops_path

    @pytest.mark.unit
    def test_all_levels_have_valid_source(self, detector):
        """全レベルが有効なソースパスを持つ"""
        for level in LEVEL_CONFIG.keys():
            result = detector.get_source_path(level)
            assert isinstance(result, Path)


# =============================================================================
# FileDetector.get_max_file_number テスト
# =============================================================================

class TestFileDetectorGetMaxFileNumber:
    """get_max_file_number メソッドのテスト"""

    @pytest.fixture
    def config(self, temp_plugin_env):
        """テスト用DigestConfig"""
        return DigestConfig(plugin_root=temp_plugin_env.plugin_root)

    @pytest.fixture
    def times_tracker(self, config):
        """テスト用DigestTimesTracker"""
        return DigestTimesTracker(config)

    @pytest.fixture
    def detector(self, config, times_tracker):
        """テスト用FileDetector"""
        return FileDetector(config, times_tracker)

    @pytest.mark.integration
    def test_returns_none_when_no_data(self, detector):
        """データがない場合はNoneを返す"""
        result = detector.get_max_file_number("weekly")
        assert result is None

    @pytest.mark.integration
    def test_returns_last_processed_when_exists(self, detector, times_tracker):
        """last_processedが存在する場合はその値を返す"""
        # last_processedを設定（input_filesを渡すことで内部でlast_processedが設定される）
        times_tracker.save("weekly", ["Loop0005_test.txt"])

        result = detector.get_max_file_number("weekly")
        assert result == "Loop0005"

    @pytest.mark.integration
    def test_returns_correct_value_for_different_levels(self, detector, times_tracker):
        """各レベルごとに正しい値を返す"""
        times_tracker.save("weekly", ["Loop0010_test.txt"])
        times_tracker.save("monthly", ["W0003_test.txt"])

        assert detector.get_max_file_number("weekly") == "Loop0010"
        assert detector.get_max_file_number("monthly") == "W0003"
        assert detector.get_max_file_number("quarterly") is None


# =============================================================================
# FileDetector.find_new_files テスト
# =============================================================================

class TestFileDetectorFindNewFiles:
    """find_new_files メソッドのテスト"""

    @pytest.fixture
    def config(self, temp_plugin_env):
        """テスト用DigestConfig"""
        return DigestConfig(plugin_root=temp_plugin_env.plugin_root)

    @pytest.fixture
    def times_tracker(self, config):
        """テスト用DigestTimesTracker"""
        return DigestTimesTracker(config)

    @pytest.fixture
    def detector(self, config, times_tracker):
        """テスト用FileDetector"""
        return FileDetector(config, times_tracker)

    @pytest.mark.integration
    def test_returns_empty_when_no_files(self, detector):
        """ファイルがない場合は空リストを返す"""
        result = detector.find_new_files("weekly")
        assert result == []

    @pytest.mark.integration
    def test_returns_all_files_on_first_run(self, detector, temp_plugin_env):
        """初回実行時（max_file_number=None）は全ファイルを返す"""
        # Loopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(temp_plugin_env.loops_path, i)

        result = detector.find_new_files("weekly")
        assert len(result) == 3

    @pytest.mark.integration
    def test_returns_only_new_files_after_last_processed(self, detector, temp_plugin_env, times_tracker):
        """last_processedより大きい番号のファイルのみ返す"""
        # Loopファイルを作成（1-5）
        for i in range(1, 6):
            create_test_loop_file(temp_plugin_env.loops_path, i)

        # last_processedをLoop0003に設定
        times_tracker.save("weekly", ["Loop0003_test.txt"])

        result = detector.find_new_files("weekly")

        # Loop0004, Loop0005のみが返される
        assert len(result) == 2
        filenames = [f.name for f in result]
        assert any("Loop0004" in name for name in filenames)
        assert any("Loop0005" in name for name in filenames)
        assert not any("Loop0003" in name for name in filenames)

    @pytest.mark.integration
    def test_returns_empty_when_no_new_files(self, detector, temp_plugin_env, times_tracker):
        """新しいファイルがない場合は空リストを返す"""
        # Loopファイルを作成（1-3）
        for i in range(1, 4):
            create_test_loop_file(temp_plugin_env.loops_path, i)

        # last_processedをLoop0003に設定（最後のファイル）
        times_tracker.save("weekly", ["Loop0003_test.txt"])

        result = detector.find_new_files("weekly")
        assert result == []

    @pytest.mark.integration
    def test_files_are_sorted(self, detector, temp_plugin_env):
        """返されるファイルはソートされている"""
        # ファイルをランダムな順序で作成
        for i in [3, 1, 5, 2, 4]:
            create_test_loop_file(temp_plugin_env.loops_path, i)

        result = detector.find_new_files("weekly")

        # ソートされていることを確認
        filenames = [f.name for f in result]
        assert filenames == sorted(filenames)

    @pytest.mark.integration
    def test_returns_empty_when_source_dir_not_exists(self, detector, temp_plugin_env):
        """ソースディレクトリが存在しない場合は空リストを返す"""
        # loops_pathを削除
        import shutil
        shutil.rmtree(temp_plugin_env.loops_path)

        result = detector.find_new_files("weekly")
        assert result == []

    @pytest.mark.integration
    def test_monthly_finds_weekly_digests(self, detector, temp_plugin_env):
        """monthlyはweekly digestファイルを検出する"""
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"

        # Weekly digestファイルを作成
        for i in range(1, 4):
            filename = f"W{i:04d}_test.txt"
            filepath = weekly_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({"test": f"weekly{i}"}, f)

        result = detector.find_new_files("monthly")
        assert len(result) == 3


# =============================================================================
# FileDetector 初期化テスト
# =============================================================================

class TestFileDetectorInit:
    """FileDetector 初期化のテスト"""

    @pytest.mark.integration
    def test_stores_config(self, temp_plugin_env):
        """configが正しく保存される"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        times_tracker = DigestTimesTracker(config)
        detector = FileDetector(config, times_tracker)
        assert detector.config is config

    @pytest.mark.integration
    def test_stores_times_tracker(self, temp_plugin_env):
        """times_trackerが正しく保存される"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        times_tracker = DigestTimesTracker(config)
        detector = FileDetector(config, times_tracker)
        assert detector.times_tracker is times_tracker

    @pytest.mark.integration
    def test_builds_level_hierarchy(self, temp_plugin_env):
        """レベル階層情報が構築される"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        times_tracker = DigestTimesTracker(config)
        detector = FileDetector(config, times_tracker)

        assert "weekly" in detector.level_hierarchy
        assert detector.level_hierarchy["weekly"]["source"] == "loops"
        assert detector.level_hierarchy["weekly"]["next"] == "monthly"

        assert "monthly" in detector.level_hierarchy
        assert detector.level_hierarchy["monthly"]["source"] == "weekly"
        assert detector.level_hierarchy["monthly"]["next"] == "quarterly"
