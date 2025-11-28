#!/usr/bin/env python3
"""
Source Path Resolver Tests
==========================

DigestConfigのget_source_dir()およびget_source_pattern()メソッドのテスト。
ソースパス解決ロジックの統一を検証。
"""

from pathlib import Path

import pytest
from test_helpers import TempPluginEnvironment

from config import DigestConfig
from domain.constants import LEVEL_CONFIG
from domain.exceptions import ConfigError

# =============================================================================
# get_source_dir のテスト
# =============================================================================


class TestGetSourceDir:
    """get_source_dir のテスト"""

    def test_weekly_returns_loops_path(self, temp_plugin_env):
        """weeklyレベルはloops_pathを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_dir("weekly")
        assert result == config.loops_path

    def test_monthly_returns_weekly_dir(self, temp_plugin_env):
        """monthlyレベルはweeklyディレクトリを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_dir("monthly")
        assert result == config.get_level_dir("weekly")

    def test_quarterly_returns_monthly_dir(self, temp_plugin_env):
        """quarterlyレベルはmonthlyディレクトリを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_dir("quarterly")
        assert result == config.get_level_dir("monthly")

    def test_annual_returns_quarterly_dir(self, temp_plugin_env):
        """annualレベルはquarterlyディレクトリを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_dir("annual")
        assert result == config.get_level_dir("quarterly")

    def test_all_levels_return_valid_paths(self, temp_plugin_env):
        """全レベルで有効なパスを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        for level in LEVEL_CONFIG.keys():
            result = config.get_source_dir(level)
            assert isinstance(result, Path)

    def test_invalid_level_raises_error(self, temp_plugin_env):
        """無効なレベルはConfigErrorを発生"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        with pytest.raises(ConfigError):
            config.get_source_dir("invalid")


# =============================================================================
# get_source_pattern のテスト
# =============================================================================


class TestGetSourcePattern:
    """get_source_pattern のテスト"""

    def test_weekly_returns_loop_pattern(self, temp_plugin_env):
        """weeklyレベルはL*.txtパターンを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_pattern("weekly")
        assert result == "L*.txt"

    def test_monthly_returns_weekly_pattern(self, temp_plugin_env):
        """monthlyレベルはW*.txtパターンを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_pattern("monthly")
        assert result == "W*.txt"

    def test_quarterly_returns_monthly_pattern(self, temp_plugin_env):
        """quarterlyレベルはM*.txtパターンを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_pattern("quarterly")
        assert result == "M*.txt"

    def test_multi_decadal_returns_decadal_pattern(self, temp_plugin_env):
        """multi_decadalレベルはD*.txtパターンを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_pattern("multi_decadal")
        assert result == "D*.txt"

    def test_centurial_returns_multi_decadal_pattern(self, temp_plugin_env):
        """centurialレベルはMD*.txtパターンを返す"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        result = config.get_source_pattern("centurial")
        assert result == "MD*.txt"

    def test_invalid_level_raises_error(self, temp_plugin_env):
        """無効なレベルはConfigErrorを発生"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        with pytest.raises(ConfigError):
            config.get_source_pattern("invalid")


# =============================================================================
# 統合テスト
# =============================================================================


class TestSourcePathIntegration:
    """ソースパス解決の統合テスト"""

    def test_source_dir_and_pattern_consistency(self, temp_plugin_env):
        """get_source_dirとget_source_patternの整合性"""
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        for level in LEVEL_CONFIG.keys():
            source_dir = config.get_source_dir(level)
            pattern = config.get_source_pattern(level)

            # パターンがプレフィックスで始まることを確認
            assert pattern.endswith("*.txt")
            # ソースディレクトリが存在することを確認
            assert source_dir.exists() or source_dir == config.loops_path
