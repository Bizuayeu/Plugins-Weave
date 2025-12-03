#!/usr/bin/env python3
"""
domain/types.py 設定型テスト
============================

設定ファイル型とTypeGuard関数のテスト。
test_types.py から分割。
"""

from typing import get_origin, get_type_hints

import pytest

from domain.types import (
    ConfigData,
    DigestTimeData,
    DigestTimesData,
    LevelsConfigData,
    PathsConfigData,
    ProvisionalDigestEntry,
    ProvisionalDigestFile,
    is_config_data,
    is_level_config_data,
    is_shadow_digest_data,
)

# =============================================================================
# 設定ファイル型テスト
# =============================================================================


class TestPathsConfigData:
    """PathsConfigData 型のテスト"""

    @pytest.mark.unit
    def test_has_directory_fields(self) -> None:
        """ディレクトリフィールドを持つ"""
        hints = get_type_hints(PathsConfigData)
        assert "loops_dir" in hints
        assert "digests_dir" in hints
        assert "essences_dir" in hints


class TestLevelsConfigData:
    """LevelsConfigData 型のテスト"""

    @pytest.mark.unit
    def test_has_threshold_fields(self) -> None:
        """しきい値フィールドを持つ"""
        hints = get_type_hints(LevelsConfigData)
        threshold_fields = [
            "weekly_threshold",
            "monthly_threshold",
            "quarterly_threshold",
            "annual_threshold",
            "triennial_threshold",
            "decadal_threshold",
            "multi_decadal_threshold",
            "centurial_threshold",
        ]
        for field in threshold_fields:
            assert field in hints, f"Missing field: {field}"


class TestConfigData:
    """ConfigData 型のテスト"""

    @pytest.mark.unit
    def test_has_base_dir_field(self) -> None:
        """base_dir フィールドを持つ"""
        hints = get_type_hints(ConfigData)
        assert "base_dir" in hints

    @pytest.mark.unit
    def test_has_paths_field(self) -> None:
        """paths フィールドを持つ"""
        hints = get_type_hints(ConfigData)
        assert "paths" in hints

    @pytest.mark.unit
    def test_has_levels_field(self) -> None:
        """levels フィールドを持つ"""
        hints = get_type_hints(ConfigData)
        assert "levels" in hints


# =============================================================================
# DigestTimes 型テスト
# =============================================================================


class TestDigestTimeData:
    """DigestTimeData 型のテスト"""

    @pytest.mark.unit
    def test_has_timestamp_field(self) -> None:
        """timestamp フィールドを持つ"""
        hints = get_type_hints(DigestTimeData)
        assert "timestamp" in hints

    @pytest.mark.unit
    def test_has_last_processed_field(self) -> None:
        """last_processed フィールドを持つ"""
        hints = get_type_hints(DigestTimeData)
        assert "last_processed" in hints


class TestDigestTimesData:
    """DigestTimesData 型のテスト"""

    @pytest.mark.unit
    def test_is_dict_type(self) -> None:
        """Dict型である"""
        # DigestTimesData = Dict[str, DigestTimeData]
        origin = get_origin(DigestTimesData)
        assert origin is dict


# =============================================================================
# Provisional Digest 型テスト
# =============================================================================


class TestProvisionalDigestEntry:
    """ProvisionalDigestEntry 型のテスト"""

    @pytest.mark.unit
    def test_has_required_fields(self) -> None:
        """必須フィールドを持つ"""
        hints = get_type_hints(ProvisionalDigestEntry)
        required_fields = ["source_file", "digest_type", "keywords", "abstract", "impression"]
        for field in required_fields:
            assert field in hints, f"Missing field: {field}"


class TestProvisionalDigestFile:
    """ProvisionalDigestFile 型のテスト"""

    @pytest.mark.unit
    def test_has_metadata_field(self) -> None:
        """metadata フィールドを持つ"""
        hints = get_type_hints(ProvisionalDigestFile)
        assert "metadata" in hints

    @pytest.mark.unit
    def test_has_individual_digests_field(self) -> None:
        """individual_digests フィールドを持つ"""
        hints = get_type_hints(ProvisionalDigestFile)
        assert "individual_digests" in hints


# =============================================================================
# TypeGuard関数テスト
# =============================================================================


class TestTypeGuards:
    """TypeGuard関数のテスト"""

    # -------------------------------------------------------------------------
    # is_config_data
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_config_data_valid_full(self) -> None:
        """有効なConfigData（全フィールド）を判定"""
        data = {"base_dir": ".", "paths": {}, "levels": {}}
        assert is_config_data(data) is True

    @pytest.mark.unit
    def test_is_config_data_valid_empty(self) -> None:
        """有効なConfigData（空dict）を判定"""
        data: dict = {}
        assert is_config_data(data) is True

    @pytest.mark.unit
    def test_is_config_data_invalid_string(self) -> None:
        """無効なデータ（文字列）を判定"""
        assert is_config_data("not a dict") is False

    @pytest.mark.unit
    def test_is_config_data_invalid_none(self) -> None:
        """無効なデータ（None）を判定"""
        assert is_config_data(None) is False

    @pytest.mark.unit
    def test_is_config_data_invalid_list(self) -> None:
        """無効なデータ（リスト）を判定"""
        assert is_config_data([]) is False

    @pytest.mark.unit
    def test_is_config_data_invalid_int(self) -> None:
        """無効なデータ（整数）を判定"""
        assert is_config_data(123) is False

    # -------------------------------------------------------------------------
    # is_level_config_data
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_level_config_data_valid(self) -> None:
        """有効なLevelConfigDataを判定"""
        data = {
            "prefix": "W",
            "digits": 4,
            "dir": "1_Weekly",
            "source": "loops",
            "next": "monthly",
        }
        assert is_level_config_data(data) is True

    @pytest.mark.unit
    def test_is_level_config_data_valid_next_none(self) -> None:
        """有効なLevelConfigData（next=None）を判定"""
        data = {
            "prefix": "C",
            "digits": 4,
            "dir": "8_Centurial",
            "source": "multi_decadal",
            "next": None,
        }
        assert is_level_config_data(data) is True

    @pytest.mark.unit
    def test_is_level_config_data_missing_prefix(self) -> None:
        """必須キー欠如（prefix）を判定"""
        data = {"digits": 4, "dir": "1_Weekly", "source": "loops", "next": "monthly"}
        assert is_level_config_data(data) is False

    @pytest.mark.unit
    def test_is_level_config_data_missing_multiple(self) -> None:
        """必須キー欠如（複数）を判定"""
        data = {"prefix": "W", "digits": 4}
        assert is_level_config_data(data) is False

    @pytest.mark.unit
    def test_is_level_config_data_invalid_type(self) -> None:
        """無効なデータ型を判定"""
        assert is_level_config_data("not a dict") is False
        assert is_level_config_data(None) is False

    # -------------------------------------------------------------------------
    # is_shadow_digest_data
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_shadow_digest_data_valid(self) -> None:
        """有効なShadowDigestDataを判定"""
        data = {
            "metadata": {"version": "2.1.0", "last_updated": "2024-01-01"},
            "latest_digests": {},
        }
        assert is_shadow_digest_data(data) is True

    @pytest.mark.unit
    def test_is_shadow_digest_data_missing_metadata(self) -> None:
        """必須キー欠如（metadata）を判定"""
        data = {"latest_digests": {}}
        assert is_shadow_digest_data(data) is False

    @pytest.mark.unit
    def test_is_shadow_digest_data_missing_latest_digests(self) -> None:
        """必須キー欠如（latest_digests）を判定"""
        data = {"metadata": {"version": "2.1.0"}}
        assert is_shadow_digest_data(data) is False

    @pytest.mark.unit
    def test_is_shadow_digest_data_invalid_type(self) -> None:
        """無効なデータ型を判定"""
        assert is_shadow_digest_data("not a dict") is False
        assert is_shadow_digest_data(None) is False
        assert is_shadow_digest_data([]) is False


# =============================================================================
# is_config_data 構造検証テスト（強化版TypeGuard）
# =============================================================================


class TestIsConfigDataStructure:
    """is_config_data の構造検証テスト（Phase 2で追加した検証ロジック）"""

    # -------------------------------------------------------------------------
    # 無効なpaths構造
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_config_data_paths_not_dict_returns_false(self) -> None:
        """pathsが文字列の場合はFalse"""
        data = {"paths": "not_a_dict"}
        assert is_config_data(data) is False

    @pytest.mark.unit
    def test_is_config_data_paths_list_returns_false(self) -> None:
        """pathsがリストの場合はFalse"""
        data = {"paths": ["item1", "item2"]}
        assert is_config_data(data) is False

    @pytest.mark.unit
    def test_is_config_data_paths_none_returns_false(self) -> None:
        """pathsがNoneの場合はFalse"""
        data = {"paths": None}
        assert is_config_data(data) is False

    @pytest.mark.unit
    def test_is_config_data_paths_int_returns_false(self) -> None:
        """pathsが整数の場合はFalse"""
        data = {"paths": 123}
        assert is_config_data(data) is False

    # -------------------------------------------------------------------------
    # 無効なlevels構造
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_config_data_levels_not_dict_returns_false(self) -> None:
        """levelsが文字列の場合はFalse"""
        data = {"levels": "not_a_dict"}
        assert is_config_data(data) is False

    @pytest.mark.unit
    def test_is_config_data_levels_list_returns_false(self) -> None:
        """levelsがリストの場合はFalse"""
        data = {"levels": [1, 2, 3]}
        assert is_config_data(data) is False

    @pytest.mark.unit
    def test_is_config_data_levels_int_returns_false(self) -> None:
        """levelsが整数の場合はFalse"""
        data = {"levels": 123}
        assert is_config_data(data) is False

    @pytest.mark.unit
    def test_is_config_data_levels_none_returns_false(self) -> None:
        """levelsがNoneの場合はFalse"""
        data = {"levels": None}
        assert is_config_data(data) is False

    # -------------------------------------------------------------------------
    # 有効なケース
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_config_data_with_valid_paths_dict(self) -> None:
        """pathsが有効なdictの場合はTrue"""
        data = {"paths": {"loops_dir": "data/Loops"}}
        assert is_config_data(data) is True

    @pytest.mark.unit
    def test_is_config_data_with_valid_levels_dict(self) -> None:
        """levelsが有効なdictの場合はTrue"""
        data = {"levels": {"weekly_threshold": 5}}
        assert is_config_data(data) is True

    @pytest.mark.unit
    def test_is_config_data_with_both_valid(self) -> None:
        """pathsとlevels両方が有効なdictの場合はTrue"""
        data = {
            "base_dir": ".",
            "paths": {"loops_dir": "data/Loops"},
            "levels": {"weekly_threshold": 5},
        }
        assert is_config_data(data) is True

    @pytest.mark.unit
    def test_is_config_data_with_empty_paths_dict(self) -> None:
        """空のpaths dictも有効"""
        data = {"paths": {}}
        assert is_config_data(data) is True

    @pytest.mark.unit
    def test_is_config_data_with_empty_levels_dict(self) -> None:
        """空のlevels dictも有効"""
        data = {"levels": {}}
        assert is_config_data(data) is True

    # -------------------------------------------------------------------------
    # 複合ケース
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_config_data_invalid_paths_valid_levels(self) -> None:
        """pathsが無効でlevelsが有効でもFalse"""
        data = {"paths": "invalid", "levels": {"threshold": 5}}
        assert is_config_data(data) is False

    @pytest.mark.unit
    def test_is_config_data_valid_paths_invalid_levels(self) -> None:
        """pathsが有効でlevelsが無効でもFalse"""
        data = {"paths": {"dir": "x"}, "levels": "invalid"}
        assert is_config_data(data) is False
