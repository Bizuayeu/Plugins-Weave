#!/usr/bin/env python3
"""
test_threshold_provider.py
==========================

config/threshold_provider.py のテスト
"""

import pytest

from config.threshold_provider import ThresholdProvider
from domain.constants import LEVEL_CONFIG, LEVEL_NAMES
from config.exceptions import ConfigError


class TestThresholdProvider:
    """ThresholdProviderクラスのテスト"""

    @pytest.fixture
    def default_config(self):
        """デフォルト設定（levels未指定）"""
        return {}

    @pytest.fixture
    def custom_config(self):
        """カスタム設定"""
        return {
            "levels": {"weekly_threshold": 10, "monthly_threshold": 8, "quarterly_threshold": 6}
        }

    @pytest.mark.unit
    @pytest.mark.parametrize("level", LEVEL_NAMES)
    def test_get_threshold_for_each_level(self, default_config, level):
        """全8レベルの閾値取得"""
        provider = ThresholdProvider(default_config)

        result = provider.get_threshold(level)

        assert isinstance(result, int)
        assert result > 0
        assert result == LEVEL_CONFIG[level].get("threshold", 5)

    @pytest.mark.unit
    def test_invalid_level_raises_config_error(self, default_config):
        """不正レベル名でConfigError"""
        provider = ThresholdProvider(default_config)

        with pytest.raises(ConfigError) as exc_info:
            provider.get_threshold("invalid_level")

        assert "Invalid level" in str(exc_info.value)
        assert "Valid levels" in str(exc_info.value)

    @pytest.mark.unit
    def test_custom_threshold_override(self, custom_config):
        """カスタム閾値の上書き"""
        provider = ThresholdProvider(custom_config)

        assert provider.get_threshold("weekly") == 10
        assert provider.get_threshold("monthly") == 8
        assert provider.get_threshold("quarterly") == 6

    @pytest.mark.unit
    def test_partial_custom_threshold(self, custom_config):
        """一部のみカスタム、残りはデフォルト"""
        provider = ThresholdProvider(custom_config)

        # カスタム設定
        assert provider.get_threshold("weekly") == 10
        # デフォルト設定（custom_configに含まれない）
        assert provider.get_threshold("annual") == LEVEL_CONFIG["annual"]["threshold"]

    @pytest.mark.unit
    def test_property_weekly_threshold(self, custom_config):
        """weekly_thresholdプロパティ"""
        provider = ThresholdProvider(custom_config)

        assert provider.weekly_threshold == 10

    @pytest.mark.unit
    def test_property_monthly_threshold(self, custom_config):
        """monthly_thresholdプロパティ"""
        provider = ThresholdProvider(custom_config)

        assert provider.monthly_threshold == 8

    @pytest.mark.unit
    def test_property_quarterly_threshold(self, custom_config):
        """quarterly_thresholdプロパティ"""
        provider = ThresholdProvider(custom_config)

        assert provider.quarterly_threshold == 6

    @pytest.mark.unit
    def test_property_annual_threshold(self, default_config):
        """annual_thresholdプロパティ（デフォルト）"""
        provider = ThresholdProvider(default_config)

        assert provider.annual_threshold == LEVEL_CONFIG["annual"]["threshold"]

    @pytest.mark.unit
    def test_property_triennial_threshold(self, default_config):
        """triennial_thresholdプロパティ（デフォルト）"""
        provider = ThresholdProvider(default_config)

        assert provider.triennial_threshold == LEVEL_CONFIG["triennial"]["threshold"]

    @pytest.mark.unit
    def test_property_decadal_threshold(self, default_config):
        """decadal_thresholdプロパティ（デフォルト）"""
        provider = ThresholdProvider(default_config)

        assert provider.decadal_threshold == LEVEL_CONFIG["decadal"]["threshold"]

    @pytest.mark.unit
    def test_property_multi_decadal_threshold(self, default_config):
        """multi_decadal_thresholdプロパティ（デフォルト）"""
        provider = ThresholdProvider(default_config)

        assert provider.multi_decadal_threshold == LEVEL_CONFIG["multi_decadal"]["threshold"]

    @pytest.mark.unit
    def test_property_centurial_threshold(self, default_config):
        """centurial_thresholdプロパティ（デフォルト）"""
        provider = ThresholdProvider(default_config)

        assert provider.centurial_threshold == LEVEL_CONFIG["centurial"]["threshold"]

    @pytest.mark.unit
    def test_empty_levels_section(self):
        """空のlevelsセクション"""
        config = {"levels": {}}
        provider = ThresholdProvider(config)

        # 全てデフォルト値になる
        assert provider.weekly_threshold == LEVEL_CONFIG["weekly"]["threshold"]

    @pytest.mark.unit
    def test_zero_threshold_allowed(self):
        """0の閾値も許容"""
        config = {"levels": {"weekly_threshold": 0}}
        provider = ThresholdProvider(config)

        assert provider.weekly_threshold == 0
