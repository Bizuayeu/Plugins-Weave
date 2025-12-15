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
from pathlib import Path
from typing import TYPE_CHECKING

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
from test_helpers import create_test_loop_file

from application.config import DigestConfig
from application.shadow import FileDetector
from application.tracking import DigestTimesTracker
from domain.constants import DIGEST_LEVEL_NAMES, LEVEL_CONFIG

# slow マーカーを適用（ファイル全体）
pytestmark = pytest.mark.slow

# =============================================================================
# FileDetector.get_source_path テスト
# =============================================================================


class TestFileDetectorGetSourcePath:
    """get_source_path メソッドのテスト"""

    @pytest.fixture
    def detector(self, temp_plugin_env: "TempPluginEnvironment"):
        """テスト用FileDetectorインスタンス"""
        config = DigestConfig()
        times_tracker = DigestTimesTracker(config)
        return FileDetector(config, times_tracker)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "level,expected_subdir",
        [
            ("monthly", "1_Weekly"),
            ("quarterly", "2_Monthly"),
            ("annual", "3_Quarterly"),
            ("triennial", "4_Annual"),
            ("decadal", "5_Triennial"),
            ("multi_decadal", "6_Decadal"),
            ("centurial", "7_Multi-decadal"),
        ],
    )
    def test_levels_return_correct_source_dir(
        self, detector, temp_plugin_env: "TempPluginEnvironment", level, expected_subdir
    ) -> None:
        """各レベルが正しいソースディレクトリを返す"""
        result = detector.get_source_path(level)
        expected = temp_plugin_env.digests_path / expected_subdir
        assert result == expected

    @pytest.mark.unit
    def test_weekly_returns_loops_path(
        self, detector, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """weeklyのソースはloops_path"""
        result = detector.get_source_path("weekly")
        assert result == temp_plugin_env.loops_path

    @pytest.mark.unit
    def test_all_digest_levels_have_valid_source(self, detector) -> None:
        """全ダイジェストレベルが有効なソースパスを持つ"""
        # Note: loop は source="raw" のため除外（ソースパスを持たない）
        for level in DIGEST_LEVEL_NAMES:
            result = detector.get_source_path(level)
            assert isinstance(result, Path)


# =============================================================================
# FileDetector.get_max_file_number テスト
# =============================================================================


class TestFileDetectorGetMaxFileNumber:
    """get_max_file_number メソッドのテスト"""

    # Note: config, times_tracker は conftest.py で定義済み

    @pytest.fixture
    def detector(self, config: "DigestConfig", times_tracker: "DigestTimesTracker"):
        """テスト用FileDetector"""
        return FileDetector(config, times_tracker)

    @pytest.mark.integration
    def test_returns_none_when_no_data(self, detector) -> None:
        """データがない場合はNoneを返す"""
        result = detector.get_max_file_number("weekly")
        assert result is None

    @pytest.mark.integration
    def test_returns_last_processed_when_exists(
        self, detector, times_tracker: "DigestTimesTracker"
    ) -> None:
        """last_processedが存在する場合はその値を返す"""
        # last_processedを設定（input_filesを渡すことで内部でlast_processedが設定される）
        times_tracker.save("weekly", ["L00005_test.txt"])

        result = detector.get_max_file_number("weekly")
        # last_processed is now stored as int (extracted number)
        assert result == 5

    @pytest.mark.integration
    def test_returns_correct_value_for_different_levels(
        self, detector, times_tracker: "DigestTimesTracker"
    ) -> None:
        """各レベルごとに正しい値を返す"""
        times_tracker.save("weekly", ["L00010_test.txt"])
        times_tracker.save("monthly", ["W0003_test.txt"])

        # last_processed is now stored as int (extracted number)
        assert detector.get_max_file_number("weekly") == 10
        assert detector.get_max_file_number("monthly") == 3
        assert detector.get_max_file_number("quarterly") is None


# =============================================================================
# FileDetector.find_new_files テスト
# =============================================================================


class TestFileDetectorFindNewFiles:
    """find_new_files メソッドのテスト"""

    # Note: config, times_tracker は conftest.py で定義済み

    @pytest.fixture
    def detector(self, config: "DigestConfig", times_tracker: "DigestTimesTracker"):
        """テスト用FileDetector"""
        return FileDetector(config, times_tracker)

    @pytest.mark.integration
    def test_returns_empty_when_no_files(self, detector) -> None:
        """ファイルがない場合は空リストを返す"""
        result = detector.find_new_files("weekly")
        assert result == []

    @pytest.mark.integration
    def test_returns_all_files_on_first_run(
        self, detector, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """初回実行時（max_file_number=None）は全ファイルを返す"""
        # Loopファイルを作成
        for i in range(1, 4):
            create_test_loop_file(temp_plugin_env.loops_path, i)

        result = detector.find_new_files("weekly")
        assert len(result) == 3

    @pytest.mark.integration
    def test_returns_only_new_files_after_last_processed(
        self,
        detector,
        temp_plugin_env: "TempPluginEnvironment",
        times_tracker: "DigestTimesTracker",
    ) -> None:
        """last_processedより大きい番号のファイルのみ返す"""
        # Loopファイルを作成（1-5）
        for i in range(1, 6):
            create_test_loop_file(temp_plugin_env.loops_path, i)

        # last_processedをL00003に設定
        # Note: find_new_files("weekly")はloop.last_processedを参照
        times_tracker.save("loop", ["L00003_test.txt"])

        result = detector.find_new_files("weekly")

        # L00004, L00005のみが返される
        assert len(result) == 2
        filenames = [f.name for f in result]
        assert any("L00004" in name for name in filenames)
        assert any("L00005" in name for name in filenames)
        assert not any("L00003" in name for name in filenames)

    @pytest.mark.integration
    def test_returns_empty_when_no_new_files(
        self,
        detector,
        temp_plugin_env: "TempPluginEnvironment",
        times_tracker: "DigestTimesTracker",
    ) -> None:
        """新しいファイルがない場合は空リストを返す"""
        # Loopファイルを作成（1-3）
        for i in range(1, 4):
            create_test_loop_file(temp_plugin_env.loops_path, i)

        # last_processedをL00003に設定（最後のファイル）
        # Note: find_new_files("weekly")はloop.last_processedを参照
        times_tracker.save("loop", ["L00003_test.txt"])

        result = detector.find_new_files("weekly")
        assert result == []

    @pytest.mark.integration
    def test_files_are_sorted(self, detector, temp_plugin_env: "TempPluginEnvironment") -> None:
        """返されるファイルはソートされている"""
        # ファイルをランダムな順序で作成
        for i in [3, 1, 5, 2, 4]:
            create_test_loop_file(temp_plugin_env.loops_path, i)

        result = detector.find_new_files("weekly")

        # ソートされていることを確認
        filenames = [f.name for f in result]
        assert filenames == sorted(filenames)

    @pytest.mark.integration
    def test_returns_empty_when_source_dir_not_exists(
        self, detector, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """ソースディレクトリが存在しない場合は空リストを返す"""
        # loops_pathを削除
        import shutil

        shutil.rmtree(temp_plugin_env.loops_path)

        result = detector.find_new_files("weekly")
        assert result == []

    @pytest.mark.integration
    def test_monthly_finds_weekly_digests(
        self, detector, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
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
    def test_stores_config(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """configが正しく保存される"""
        config = DigestConfig()
        times_tracker = DigestTimesTracker(config)
        detector = FileDetector(config, times_tracker)
        assert detector.config is config

    @pytest.mark.integration
    def test_stores_times_tracker(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """times_trackerが正しく保存される"""
        config = DigestConfig()
        times_tracker = DigestTimesTracker(config)
        detector = FileDetector(config, times_tracker)
        assert detector.times_tracker is times_tracker

    @pytest.mark.integration
    def test_builds_level_hierarchy(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """レベル階層情報が構築される"""
        config = DigestConfig()
        times_tracker = DigestTimesTracker(config)
        detector = FileDetector(config, times_tracker)

        assert "weekly" in detector.level_hierarchy
        assert detector.level_hierarchy["weekly"]["source"] == "loops"
        assert detector.level_hierarchy["weekly"]["next"] == "monthly"

        assert "monthly" in detector.level_hierarchy
        assert detector.level_hierarchy["monthly"]["source"] == "weekly"
        assert detector.level_hierarchy["monthly"]["next"] == "quarterly"


# =============================================================================
# FileDetector._get_detection_level テスト
# =============================================================================


class TestFileDetectorGetDetectionLevel:
    """_get_detection_level メソッドのテスト"""

    @pytest.fixture
    def detector(self, config: "DigestConfig", times_tracker: "DigestTimesTracker"):
        """テスト用FileDetector"""
        return FileDetector(config, times_tracker)

    @pytest.mark.unit
    def test_weekly_returns_loop(self, detector) -> None:
        """weeklyレベルは loop を参照する"""
        result = detector._get_detection_level("weekly")
        assert result == "loop"

    @pytest.mark.unit
    def test_monthly_returns_weekly(self, detector) -> None:
        """monthlyレベルは weekly を参照する（ソースはweekly）"""
        result = detector._get_detection_level("monthly")
        assert result == "weekly"

    @pytest.mark.unit
    def test_quarterly_returns_monthly(self, detector) -> None:
        """quarterlyレベルは monthly を参照する"""
        result = detector._get_detection_level("quarterly")
        assert result == "monthly"

    @pytest.mark.unit
    def test_annual_returns_quarterly(self, detector) -> None:
        """annualレベルは quarterly を参照する"""
        result = detector._get_detection_level("annual")
        assert result == "quarterly"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "level,expected_source",
        [
            ("triennial", "annual"),
            ("decadal", "triennial"),
            ("multi_decadal", "decadal"),
            ("centurial", "multi_decadal"),
        ],
    )
    def test_higher_levels_return_source_level(self, detector, level, expected_source) -> None:
        """上位レベルはそれぞれのソースレベルを参照する"""
        result = detector._get_detection_level(level)
        assert result == expected_source


class TestFileDetectorFindNewFilesUsesLoopLevel:
    """find_new_files が loop レベルを使用することを検証"""

    @pytest.fixture
    def detector(self, config: "DigestConfig", times_tracker: "DigestTimesTracker"):
        """テスト用FileDetector"""
        return FileDetector(config, times_tracker)

    @pytest.mark.integration
    def test_find_new_files_uses_loop_level_for_weekly(
        self,
        detector,
        temp_plugin_env: "TempPluginEnvironment",
        times_tracker: "DigestTimesTracker",
    ) -> None:
        """weeklyのfind_new_filesがloop.last_processedを参照"""
        # Loopファイルを作成（254-258）
        for i in range(254, 259):
            create_test_loop_file(temp_plugin_env.loops_path, i)

        # loop.last_processed = 255 に設定
        times_tracker.save("loop", ["L00255_test.txt"])

        result = detector.find_new_files("weekly")

        # L00256, L00257, L00258 のみが検出される（255より後）
        assert len(result) == 3
        filenames = [f.name for f in result]
        assert any("L00256" in name for name in filenames)
        assert any("L00257" in name for name in filenames)
        assert any("L00258" in name for name in filenames)
        assert not any("L00255" in name for name in filenames)


class TestFileDetectorFindNewFilesUsesSourceLevel:
    """find_new_files がソースレベルの last_processed を使用することを検証"""

    @pytest.fixture
    def detector(self, config: "DigestConfig", times_tracker: "DigestTimesTracker"):
        """テスト用FileDetector"""
        return FileDetector(config, times_tracker)

    @pytest.mark.integration
    def test_monthly_find_new_files_uses_weekly_last_processed(
        self,
        detector,
        temp_plugin_env: "TempPluginEnvironment",
        times_tracker: "DigestTimesTracker",
        config: "DigestConfig",
    ) -> None:
        """
        Monthly新規ファイル検出は weekly.last_processed を参照する

        Setup:
          - weekly.last_processed = 52
          - monthly.last_processed = 10
          - W0050.txt, W0051.txt, W0052.txt, W0053.txt が存在

        Expected:
          - find_new_files("monthly") → [W0053.txt] のみ検出
          - （W0052以下は既に処理済み）
        """
        # Setup: Weeklyディレクトリを作成しファイルを配置
        weekly_dir = config.digests_path / "1_Weekly"
        weekly_dir.mkdir(parents=True, exist_ok=True)
        for i in [50, 51, 52, 53]:
            (weekly_dir / f"W00{i}_Test.txt").touch()

        # Setup: last_digest_times を設定
        times_tracker.save_digest_number("weekly", 52)
        times_tracker.save_digest_number("monthly", 10)

        # Execute
        result = detector.find_new_files("monthly")

        # Assert: W0053 のみ検出（W0052までは処理済み）
        assert len(result) == 1
        assert "W0053" in result[0].name

    @pytest.mark.integration
    def test_quarterly_find_new_files_uses_monthly_last_processed(
        self,
        detector,
        temp_plugin_env: "TempPluginEnvironment",
        times_tracker: "DigestTimesTracker",
        config: "DigestConfig",
    ) -> None:
        """
        Quarterly新規ファイル検出は monthly.last_processed を参照する
        """
        # Setup: Monthlyディレクトリを作成しファイルを配置
        monthly_dir = config.digests_path / "2_Monthly"
        monthly_dir.mkdir(parents=True, exist_ok=True)
        for i in [8, 9, 10, 11]:
            (monthly_dir / f"M00{i:02d}_Test.txt").touch()

        # Setup: last_digest_times を設定
        times_tracker.save_digest_number("monthly", 10)
        times_tracker.save_digest_number("quarterly", 3)

        # Execute
        result = detector.find_new_files("quarterly")

        # Assert: M0011 のみ検出（M0010までは処理済み）
        assert len(result) == 1
        assert "M0011" in result[0].name
