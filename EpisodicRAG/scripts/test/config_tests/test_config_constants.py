#!/usr/bin/env python3
"""
config_constants モジュールのテスト
===================================

config/config_constants.py で定義された共有定数のテスト。
定数の存在、型、値を検証する。
"""

import pytest

from domain.config.config_constants import REQUIRED_CONFIG_KEYS, THRESHOLD_KEYS

pytestmark = pytest.mark.unit


class TestRequiredConfigKeys:
    """REQUIRED_CONFIG_KEYS定数のテスト"""

    def test_required_keys_is_list(self) -> None:
        """REQUIRED_CONFIG_KEYSがリストであること"""
        assert isinstance(REQUIRED_CONFIG_KEYS, list)

    def test_required_keys_not_empty(self) -> None:
        """REQUIRED_CONFIG_KEYSが空でないこと"""
        assert len(REQUIRED_CONFIG_KEYS) > 0

    def test_required_keys_contains_essential_paths(self) -> None:
        """必須パスキーが含まれていること"""
        assert "loops_path" in REQUIRED_CONFIG_KEYS
        assert "digests_path" in REQUIRED_CONFIG_KEYS
        assert "essences_path" in REQUIRED_CONFIG_KEYS

    def test_required_keys_are_strings(self) -> None:
        """すべてのキーが文字列であること"""
        for key in REQUIRED_CONFIG_KEYS:
            assert isinstance(key, str), f"Key '{key}' is not a string"

    def test_required_keys_count(self) -> None:
        """必須キーが3つであること"""
        assert len(REQUIRED_CONFIG_KEYS) == 3


class TestThresholdKeys:
    """THRESHOLD_KEYS定数のテスト"""

    def test_threshold_keys_is_list(self) -> None:
        """THRESHOLD_KEYSがリストであること"""
        assert isinstance(THRESHOLD_KEYS, list)

    def test_threshold_keys_count(self) -> None:
        """8レベル分の閾値キーが存在すること"""
        assert len(THRESHOLD_KEYS) == 8

    def test_threshold_keys_are_strings(self) -> None:
        """すべてのキーが文字列であること"""
        for key in THRESHOLD_KEYS:
            assert isinstance(key, str), f"Key '{key}' is not a string"

    @pytest.mark.parametrize(
        "level",
        [
            "weekly",
            "monthly",
            "quarterly",
            "annual",
            "triennial",
            "decadal",
            "multi_decadal",
            "centurial",
        ],
    )
    def test_threshold_key_for_each_level(self, level) -> None:
        """各レベルの閾値キーが存在すること"""
        expected_key = f"{level}_threshold"
        assert expected_key in THRESHOLD_KEYS, f"Missing threshold key: {expected_key}"

    def test_threshold_keys_naming_convention(self) -> None:
        """すべての閾値キーが '_threshold' で終わること"""
        for key in THRESHOLD_KEYS:
            assert key.endswith("_threshold"), f"Key '{key}' should end with '_threshold'"
