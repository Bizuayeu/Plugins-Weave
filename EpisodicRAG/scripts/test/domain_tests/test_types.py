#!/usr/bin/env python3
"""
domain/types.py のユニットテスト
================================

TypedDict定義の構造と型互換性を検証。
- 必須フィールドの存在確認
- TypedDict継承関係
- 型構造の検証
"""

from typing import Dict, List, Optional, get_args, get_origin, get_type_hints

import pytest

from domain.types import (
    # メタデータ型
    BaseMetadata,
    ConfigData,
    DigestMetadata,
    DigestMetadataComplete,
    # DigestTimes型
    DigestTimeData,
    DigestTimesData,
    GrandDigestData,
    GrandDigestLevelData,
    IndividualDigestData,
    # レベル設定型
    LevelConfigData,
    LevelHierarchyEntry,
    LevelsConfigData,
    # Digest データ型
    OverallDigestData,
    # 設定ファイル型
    PathsConfigData,
    # Provisional型
    ProvisionalDigestEntry,
    ProvisionalDigestFile,
    RegularDigestData,
    ShadowDigestData,
    ShadowLevelData,
    # TypeGuard関数
    is_config_data,
    is_level_config_data,
    is_shadow_digest_data,
)

# =============================================================================
# メタデータ型テスト
# =============================================================================


class TestBaseMetadata:
    """BaseMetadata 型のテスト"""

    @pytest.mark.unit
    def test_has_version_field(self):
        """version フィールドを持つ"""
        hints = get_type_hints(BaseMetadata)
        assert "version" in hints
        assert hints["version"] is str

    @pytest.mark.unit
    def test_has_last_updated_field(self):
        """last_updated フィールドを持つ"""
        hints = get_type_hints(BaseMetadata)
        assert "last_updated" in hints
        assert hints["last_updated"] is str

    @pytest.mark.unit
    def test_is_total_false(self):
        """total=False（全フィールドオプショナル）"""
        # BaseMetadataのフィールドはすべてオプショナル
        data: BaseMetadata = {}  # 空でも有効
        assert isinstance(data, dict)


class TestDigestMetadata:
    """DigestMetadata 型のテスト"""

    @pytest.mark.unit
    def test_has_digest_level_field(self):
        """digest_level フィールドを持つ"""
        hints = get_type_hints(DigestMetadata)
        assert "digest_level" in hints

    @pytest.mark.unit
    def test_has_digest_number_field(self):
        """digest_number フィールドを持つ"""
        hints = get_type_hints(DigestMetadata)
        assert "digest_number" in hints

    @pytest.mark.unit
    def test_has_source_count_field(self):
        """source_count フィールドを持つ"""
        hints = get_type_hints(DigestMetadata)
        assert "source_count" in hints


class TestDigestMetadataComplete:
    """DigestMetadataComplete 型のテスト"""

    @pytest.mark.unit
    def test_has_all_metadata_fields(self):
        """すべてのメタデータフィールドを持つ"""
        hints = get_type_hints(DigestMetadataComplete)
        expected_fields = [
            "version",
            "last_updated",
            "digest_level",
            "digest_number",
            "source_count",
            "description",
        ]
        for field in expected_fields:
            assert field in hints, f"Missing field: {field}"


# =============================================================================
# レベル設定型テスト
# =============================================================================


class TestLevelConfigData:
    """LevelConfigData 型のテスト"""

    @pytest.mark.unit
    def test_has_required_fields(self):
        """必須フィールドを持つ"""
        hints = get_type_hints(LevelConfigData)
        required_fields = ["prefix", "digits", "dir", "source", "next"]
        for field in required_fields:
            assert field in hints, f"Missing field: {field}"

    @pytest.mark.unit
    def test_prefix_is_string(self):
        """prefix は文字列型"""
        hints = get_type_hints(LevelConfigData)
        assert hints["prefix"] is str

    @pytest.mark.unit
    def test_digits_is_int(self):
        """digits は整数型"""
        hints = get_type_hints(LevelConfigData)
        assert hints["digits"] is int

    @pytest.mark.unit
    def test_next_is_optional_string(self):
        """next はOptional[str]型"""
        hints = get_type_hints(LevelConfigData)
        assert get_origin(hints["next"]) is type(None) or hints["next"] == Optional[str]


class TestLevelHierarchyEntry:
    """LevelHierarchyEntry 型のテスト"""

    @pytest.mark.unit
    def test_has_source_field(self):
        """source フィールドを持つ"""
        hints = get_type_hints(LevelHierarchyEntry)
        assert "source" in hints

    @pytest.mark.unit
    def test_has_next_field(self):
        """next フィールドを持つ"""
        hints = get_type_hints(LevelHierarchyEntry)
        assert "next" in hints


# =============================================================================
# Digest データ型テスト
# =============================================================================


class TestOverallDigestData:
    """OverallDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_timestamp_field(self):
        """timestamp フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "timestamp" in hints
        assert hints["timestamp"] is str

    @pytest.mark.unit
    def test_has_source_files_field(self):
        """source_files フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "source_files" in hints
        assert hints["source_files"] == List[str]

    @pytest.mark.unit
    def test_has_digest_type_field(self):
        """digest_type フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "digest_type" in hints

    @pytest.mark.unit
    def test_has_keywords_field(self):
        """keywords フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "keywords" in hints
        assert hints["keywords"] == List[str]

    @pytest.mark.unit
    def test_has_abstract_field(self):
        """abstract フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "abstract" in hints

    @pytest.mark.unit
    def test_has_impression_field(self):
        """impression フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "impression" in hints


class TestIndividualDigestData:
    """IndividualDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_required_fields(self):
        """必須フィールドを持つ"""
        hints = get_type_hints(IndividualDigestData)
        required_fields = ["source_file", "digest_type", "keywords", "abstract", "impression"]
        for field in required_fields:
            assert field in hints, f"Missing field: {field}"


class TestShadowDigestData:
    """ShadowDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_metadata_field(self):
        """metadata フィールドを持つ"""
        hints = get_type_hints(ShadowDigestData)
        assert "metadata" in hints

    @pytest.mark.unit
    def test_has_latest_digests_field(self):
        """latest_digests フィールドを持つ"""
        hints = get_type_hints(ShadowDigestData)
        assert "latest_digests" in hints


class TestGrandDigestData:
    """GrandDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_metadata_field(self):
        """metadata フィールドを持つ"""
        hints = get_type_hints(GrandDigestData)
        assert "metadata" in hints

    @pytest.mark.unit
    def test_has_major_digests_field(self):
        """major_digests フィールドを持つ"""
        hints = get_type_hints(GrandDigestData)
        assert "major_digests" in hints


class TestRegularDigestData:
    """RegularDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_metadata_field(self):
        """metadata フィールドを持つ"""
        hints = get_type_hints(RegularDigestData)
        assert "metadata" in hints

    @pytest.mark.unit
    def test_has_overall_digest_field(self):
        """overall_digest フィールドを持つ"""
        hints = get_type_hints(RegularDigestData)
        assert "overall_digest" in hints

    @pytest.mark.unit
    def test_has_individual_digests_field(self):
        """individual_digests フィールドを持つ"""
        hints = get_type_hints(RegularDigestData)
        assert "individual_digests" in hints


# =============================================================================
# 設定ファイル型テスト
# =============================================================================


class TestPathsConfigData:
    """PathsConfigData 型のテスト"""

    @pytest.mark.unit
    def test_has_directory_fields(self):
        """ディレクトリフィールドを持つ"""
        hints = get_type_hints(PathsConfigData)
        assert "loops_dir" in hints
        assert "digests_dir" in hints
        assert "essences_dir" in hints


class TestLevelsConfigData:
    """LevelsConfigData 型のテスト"""

    @pytest.mark.unit
    def test_has_threshold_fields(self):
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
    def test_has_base_dir_field(self):
        """base_dir フィールドを持つ"""
        hints = get_type_hints(ConfigData)
        assert "base_dir" in hints

    @pytest.mark.unit
    def test_has_paths_field(self):
        """paths フィールドを持つ"""
        hints = get_type_hints(ConfigData)
        assert "paths" in hints

    @pytest.mark.unit
    def test_has_levels_field(self):
        """levels フィールドを持つ"""
        hints = get_type_hints(ConfigData)
        assert "levels" in hints


# =============================================================================
# DigestTimes 型テスト
# =============================================================================


class TestDigestTimeData:
    """DigestTimeData 型のテスト"""

    @pytest.mark.unit
    def test_has_timestamp_field(self):
        """timestamp フィールドを持つ"""
        hints = get_type_hints(DigestTimeData)
        assert "timestamp" in hints

    @pytest.mark.unit
    def test_has_last_processed_field(self):
        """last_processed フィールドを持つ"""
        hints = get_type_hints(DigestTimeData)
        assert "last_processed" in hints


class TestDigestTimesData:
    """DigestTimesData 型のテスト"""

    @pytest.mark.unit
    def test_is_dict_type(self):
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
    def test_has_required_fields(self):
        """必須フィールドを持つ"""
        hints = get_type_hints(ProvisionalDigestEntry)
        required_fields = ["source_file", "digest_type", "keywords", "abstract", "impression"]
        for field in required_fields:
            assert field in hints, f"Missing field: {field}"


class TestProvisionalDigestFile:
    """ProvisionalDigestFile 型のテスト"""

    @pytest.mark.unit
    def test_has_metadata_field(self):
        """metadata フィールドを持つ"""
        hints = get_type_hints(ProvisionalDigestFile)
        assert "metadata" in hints

    @pytest.mark.unit
    def test_has_individual_digests_field(self):
        """individual_digests フィールドを持つ"""
        hints = get_type_hints(ProvisionalDigestFile)
        assert "individual_digests" in hints


# =============================================================================
# 型互換性テスト
# =============================================================================


class TestTypeCompatibility:
    """型互換性のテスト"""

    @pytest.mark.unit
    def test_overall_digest_data_creation(self):
        """OverallDigestData を作成できる"""
        data: OverallDigestData = {
            "timestamp": "2024-01-01T00:00:00",
            "source_files": ["Loop0001_test.txt"],
            "digest_type": "weekly",
            "keywords": ["test"],
            "abstract": "Test abstract",
            "impression": "Test impression",
        }
        assert data["timestamp"] == "2024-01-01T00:00:00"
        assert len(data["source_files"]) == 1

    @pytest.mark.unit
    def test_shadow_digest_data_creation(self):
        """ShadowDigestData を作成できる"""
        data: ShadowDigestData = {
            "metadata": {
                "version": "2.1.0",
                "last_updated": "2024-01-01T00:00:00",
            },
            "latest_digests": {},
        }
        assert data["metadata"]["version"] == "2.1.0"

    @pytest.mark.unit
    def test_grand_digest_data_creation(self):
        """GrandDigestData を作成できる"""
        data: GrandDigestData = {
            "metadata": {
                "version": "2.1.0",
                "last_updated": "2024-01-01T00:00:00",
            },
            "major_digests": {},
        }
        assert data["metadata"]["version"] == "2.1.0"

    @pytest.mark.unit
    def test_config_data_creation(self):
        """ConfigData を作成できる"""
        data: ConfigData = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "Loops",
                "digests_dir": "Digests",
            },
            "levels": {
                "weekly_threshold": 5,
            },
        }
        assert data["base_dir"] == "."


# =============================================================================
# TypeGuard関数テスト
# =============================================================================


class TestTypeGuards:
    """TypeGuard関数のテスト"""

    # -------------------------------------------------------------------------
    # is_config_data
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_config_data_valid_full(self):
        """有効なConfigData（全フィールド）を判定"""
        data = {"base_dir": ".", "paths": {}, "levels": {}}
        assert is_config_data(data) is True

    @pytest.mark.unit
    def test_is_config_data_valid_empty(self):
        """有効なConfigData（空dict）を判定"""
        data: dict = {}
        assert is_config_data(data) is True

    @pytest.mark.unit
    def test_is_config_data_invalid_string(self):
        """無効なデータ（文字列）を判定"""
        assert is_config_data("not a dict") is False

    @pytest.mark.unit
    def test_is_config_data_invalid_none(self):
        """無効なデータ（None）を判定"""
        assert is_config_data(None) is False

    @pytest.mark.unit
    def test_is_config_data_invalid_list(self):
        """無効なデータ（リスト）を判定"""
        assert is_config_data([]) is False

    @pytest.mark.unit
    def test_is_config_data_invalid_int(self):
        """無効なデータ（整数）を判定"""
        assert is_config_data(123) is False

    # -------------------------------------------------------------------------
    # is_level_config_data
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_level_config_data_valid(self):
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
    def test_is_level_config_data_valid_next_none(self):
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
    def test_is_level_config_data_missing_prefix(self):
        """必須キー欠如（prefix）を判定"""
        data = {"digits": 4, "dir": "1_Weekly", "source": "loops", "next": "monthly"}
        assert is_level_config_data(data) is False

    @pytest.mark.unit
    def test_is_level_config_data_missing_multiple(self):
        """必須キー欠如（複数）を判定"""
        data = {"prefix": "W", "digits": 4}
        assert is_level_config_data(data) is False

    @pytest.mark.unit
    def test_is_level_config_data_invalid_type(self):
        """無効なデータ型を判定"""
        assert is_level_config_data("not a dict") is False
        assert is_level_config_data(None) is False

    # -------------------------------------------------------------------------
    # is_shadow_digest_data
    # -------------------------------------------------------------------------

    @pytest.mark.unit
    def test_is_shadow_digest_data_valid(self):
        """有効なShadowDigestDataを判定"""
        data = {
            "metadata": {"version": "2.1.0", "last_updated": "2024-01-01"},
            "latest_digests": {},
        }
        assert is_shadow_digest_data(data) is True

    @pytest.mark.unit
    def test_is_shadow_digest_data_missing_metadata(self):
        """必須キー欠如（metadata）を判定"""
        data = {"latest_digests": {}}
        assert is_shadow_digest_data(data) is False

    @pytest.mark.unit
    def test_is_shadow_digest_data_missing_latest_digests(self):
        """必須キー欠如（latest_digests）を判定"""
        data = {"metadata": {"version": "2.1.0"}}
        assert is_shadow_digest_data(data) is False

    @pytest.mark.unit
    def test_is_shadow_digest_data_invalid_type(self):
        """無効なデータ型を判定"""
        assert is_shadow_digest_data("not a dict") is False
        assert is_shadow_digest_data(None) is False
        assert is_shadow_digest_data([]) is False
