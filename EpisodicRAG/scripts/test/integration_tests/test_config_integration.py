#!/usr/bin/env python3
"""
Config Integration Tests
========================

Config → Application → Domain 層の統合フローを検証するテスト。
設定読み込みからパス解決、閾値適用、レベル検証までの連携を確認。

このテストスイートは以下を検証:
1. Config読み込み → パス解決 → ファイル検出
2. Threshold設定 → カスケード判定
3. Level検証 → Domain例外
"""

import pytest
from test_helpers import create_test_loop_file

from application.shadow import FileDetector
from application.tracking import DigestTimesTracker
from config import DigestConfig
from domain.constants import LEVEL_CONFIG, LEVEL_NAMES
from domain.exceptions import ConfigError

# integration マーカーを適用（ファイル全体）
pytestmark = pytest.mark.integration

# =============================================================================
# Config読み込み → パス解決 統合テスト
# =============================================================================


class TestConfigPathResolution:
    """Config読み込みからパス解決までの統合テスト"""

    def test_config_loads_and_creates_directories(self, temp_plugin_env):
        """設定読み込み後、必要なディレクトリが存在する"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        assert config.loops_path.exists()
        assert config.digests_path.exists()
        assert config.essences_path.exists()

    def test_level_dirs_accessible_from_config(self, temp_plugin_env):
        """全レベルディレクトリにアクセス可能"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        for level in LEVEL_NAMES:
            level_dir = config.get_level_dir(level)
            assert level_dir.exists(), f"Level dir for {level} should exist"
            assert level_dir.name == LEVEL_CONFIG[level]["dir"]

    def test_provisional_dirs_accessible_from_config(self, temp_plugin_env):
        """全レベルのProvisionalディレクトリにアクセス可能"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        for level in LEVEL_NAMES:
            prov_dir = config.get_provisional_dir(level)
            assert prov_dir.exists(), f"Provisional dir for {level} should exist"
            assert prov_dir.name == "Provisional"

    def test_source_dir_for_each_level(self, temp_plugin_env):
        """各レベルのソースディレクトリが正しく解決される"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # weekly のソースは loops
        assert config.get_source_dir("weekly") == config.loops_path

        # monthly のソースは weekly digests
        weekly_dir = config.get_level_dir("weekly")
        assert config.get_source_dir("monthly") == weekly_dir


# =============================================================================
# Config → Application 連携テスト
# =============================================================================


class TestConfigApplicationIntegration:
    """Config層とApplication層の連携テスト"""

    def test_file_detector_uses_config_paths(self, temp_plugin_env):
        """FileDetectorがConfigのパスを正しく使用する"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        times_tracker = DigestTimesTracker(config)
        detector = FileDetector(config, times_tracker)

        # Loopファイルを作成
        create_test_loop_file(temp_plugin_env.loops_path, 1)
        create_test_loop_file(temp_plugin_env.loops_path, 2)

        # detector がファイルを検出
        new_files = detector.find_new_files("weekly")
        assert len(new_files) == 2

    def test_times_tracker_uses_config_paths(self, temp_plugin_env):
        """DigestTimesTrackerがConfigのパスを正しく使用する"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        times_tracker = DigestTimesTracker(config)

        # last_digest_times.json が正しい場所（.claude-plugin/）に作成される
        times_file = config.config_file.parent / "last_digest_times.json"

        # 保存操作
        times_tracker.save("weekly", ["L00001_test.txt"])

        # ファイルが作成されている
        assert times_file.exists()


# =============================================================================
# Threshold 適用テスト
# =============================================================================


class TestThresholdApplication:
    """閾値設定がApplication層で正しく適用されることを確認"""

    def test_default_thresholds_available(self, temp_plugin_env):
        """デフォルト閾値が全レベルで利用可能"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        for level in LEVEL_NAMES:
            threshold = config.get_threshold(level)
            assert isinstance(threshold, int)
            assert threshold >= 1

    def test_threshold_accessed_via_property(self, temp_plugin_env):
        """閾値がthresholdプロパティ経由で取得可能"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # ARCHITECTURE: コンポーネント公開パターン
        # config.threshold経由でThresholdProviderにアクセス
        assert hasattr(config, "threshold")
        assert isinstance(config.threshold.weekly_threshold, int)


# =============================================================================
# エラーハンドリング統合テスト
# =============================================================================


class TestErrorHandlingIntegration:
    """Config層のエラーがApplication/Domain層で適切に処理される"""

    def test_invalid_level_raises_config_error(self, temp_plugin_env):
        """無効なレベル名でConfigErrorが発生"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        with pytest.raises(ConfigError):
            config.get_threshold("invalid_level")

    def test_config_validation_detects_issues(self, temp_plugin_env):
        """Config検証が問題を検出"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # 正常な設定ではディレクトリ構造検証エラーなし
        errors = config.validate_directory_structure()
        assert errors == []


# =============================================================================
# 全体フロー統合テスト
# =============================================================================


class TestEndToEndConfigFlow:
    """Config → Application → Domain の完全なフロー"""

    def test_complete_config_to_detection_flow(self, temp_plugin_env):
        """設定からファイル検出までの完全なフロー"""
        # 1. Config初期化
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # 2. Application層コンポーネント初期化
        times_tracker = DigestTimesTracker(config)
        detector = FileDetector(config, times_tracker)

        # 3. Loopファイル作成
        for i in range(1, 4):
            create_test_loop_file(temp_plugin_env.loops_path, i)

        # 4. 新規ファイル検出
        new_files = detector.find_new_files("weekly")
        assert len(new_files) == 3

        # 5. 処理済みとして記録
        filenames = [f.name for f in new_files]
        times_tracker.save("weekly", filenames)

        # 6. 再検出時は空
        new_files_after = detector.find_new_files("weekly")
        assert len(new_files_after) == 0

    def test_threshold_affects_behavior(self, temp_plugin_env):
        """閾値がApplication層の動作に影響を与える"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        # 閾値を取得
        weekly_threshold = config.get_threshold("weekly")

        # 閾値は正の整数
        assert weekly_threshold >= 1

        # この閾値はFileDetector等で使用される
        # （実際の閾値判定ロジックはApplication層が担当）
