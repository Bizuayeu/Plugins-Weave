#!/usr/bin/env python3
"""
domain/types.py Digest型テスト
==============================

Digestデータ型と型互換性のテスト。
test_types.py から分割。
"""

from typing import List, get_type_hints

import pytest

from domain.types import (
    ConfigData,
    GrandDigestData,
    IndividualDigestData,
    OverallDigestData,
    RegularDigestData,
    ShadowDigestData,
)

# =============================================================================
# Digest データ型テスト
# =============================================================================


class TestOverallDigestData:
    """OverallDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_timestamp_field(self) -> None:
        """timestamp フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "timestamp" in hints
        assert hints["timestamp"] is str

    @pytest.mark.unit
    def test_has_source_files_field(self) -> None:
        """source_files フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "source_files" in hints
        assert hints["source_files"] == List[str]

    @pytest.mark.unit
    def test_has_digest_type_field(self) -> None:
        """digest_type フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "digest_type" in hints

    @pytest.mark.unit
    def test_has_keywords_field(self) -> None:
        """keywords フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "keywords" in hints
        assert hints["keywords"] == List[str]

    @pytest.mark.unit
    def test_has_abstract_field(self) -> None:
        """abstract フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "abstract" in hints

    @pytest.mark.unit
    def test_has_impression_field(self) -> None:
        """impression フィールドを持つ"""
        hints = get_type_hints(OverallDigestData)
        assert "impression" in hints


class TestIndividualDigestData:
    """IndividualDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_required_fields(self) -> None:
        """必須フィールドを持つ"""
        hints = get_type_hints(IndividualDigestData)
        required_fields = ["source_file", "digest_type", "keywords", "abstract", "impression"]
        for field in required_fields:
            assert field in hints, f"Missing field: {field}"


class TestShadowDigestData:
    """ShadowDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_metadata_field(self) -> None:
        """metadata フィールドを持つ"""
        hints = get_type_hints(ShadowDigestData)
        assert "metadata" in hints

    @pytest.mark.unit
    def test_has_latest_digests_field(self) -> None:
        """latest_digests フィールドを持つ"""
        hints = get_type_hints(ShadowDigestData)
        assert "latest_digests" in hints


class TestGrandDigestData:
    """GrandDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_metadata_field(self) -> None:
        """metadata フィールドを持つ"""
        hints = get_type_hints(GrandDigestData)
        assert "metadata" in hints

    @pytest.mark.unit
    def test_has_major_digests_field(self) -> None:
        """major_digests フィールドを持つ"""
        hints = get_type_hints(GrandDigestData)
        assert "major_digests" in hints


class TestRegularDigestData:
    """RegularDigestData 型のテスト"""

    @pytest.mark.unit
    def test_has_metadata_field(self) -> None:
        """metadata フィールドを持つ"""
        hints = get_type_hints(RegularDigestData)
        assert "metadata" in hints

    @pytest.mark.unit
    def test_has_overall_digest_field(self) -> None:
        """overall_digest フィールドを持つ"""
        hints = get_type_hints(RegularDigestData)
        assert "overall_digest" in hints

    @pytest.mark.unit
    def test_has_individual_digests_field(self) -> None:
        """individual_digests フィールドを持つ"""
        hints = get_type_hints(RegularDigestData)
        assert "individual_digests" in hints


# =============================================================================
# 型互換性テスト
# =============================================================================


class TestTypeCompatibility:
    """型互換性のテスト"""

    @pytest.mark.unit
    def test_overall_digest_data_creation(self) -> None:
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
    def test_shadow_digest_data_creation(self) -> None:
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
    def test_grand_digest_data_creation(self) -> None:
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
    def test_config_data_creation(self) -> None:
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
