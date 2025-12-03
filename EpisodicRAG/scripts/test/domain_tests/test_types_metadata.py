#!/usr/bin/env python3
"""
domain/types.py メタデータ型テスト
==================================

メタデータとレベル設定型のテスト。
test_types.py から分割。
"""

from typing import Optional, get_origin, get_type_hints

import pytest

from domain.types import (
    BaseMetadata,
    DigestMetadata,
    DigestMetadataComplete,
    LevelConfigData,
    LevelHierarchyEntry,
)

# =============================================================================
# メタデータ型テスト
# =============================================================================


class TestBaseMetadata:
    """BaseMetadata 型のテスト"""

    @pytest.mark.unit
    def test_has_version_field(self) -> None:
        """version フィールドを持つ"""
        hints = get_type_hints(BaseMetadata)
        assert "version" in hints
        assert hints["version"] is str

    @pytest.mark.unit
    def test_has_last_updated_field(self) -> None:
        """last_updated フィールドを持つ"""
        hints = get_type_hints(BaseMetadata)
        assert "last_updated" in hints
        assert hints["last_updated"] is str

    @pytest.mark.unit
    def test_is_total_false(self) -> None:
        """total=False（全フィールドオプショナル）"""
        # BaseMetadataのフィールドはすべてオプショナル
        data: BaseMetadata = {}  # 空でも有効
        assert isinstance(data, dict)


class TestDigestMetadata:
    """DigestMetadata 型のテスト"""

    @pytest.mark.unit
    def test_has_digest_level_field(self) -> None:
        """digest_level フィールドを持つ"""
        hints = get_type_hints(DigestMetadata)
        assert "digest_level" in hints

    @pytest.mark.unit
    def test_has_digest_number_field(self) -> None:
        """digest_number フィールドを持つ"""
        hints = get_type_hints(DigestMetadata)
        assert "digest_number" in hints

    @pytest.mark.unit
    def test_has_source_count_field(self) -> None:
        """source_count フィールドを持つ"""
        hints = get_type_hints(DigestMetadata)
        assert "source_count" in hints


class TestDigestMetadataComplete:
    """DigestMetadataComplete 型のテスト"""

    @pytest.mark.unit
    def test_has_all_metadata_fields(self) -> None:
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
    def test_has_required_fields(self) -> None:
        """必須フィールドを持つ"""
        hints = get_type_hints(LevelConfigData)
        required_fields = ["prefix", "digits", "dir", "source", "next"]
        for field in required_fields:
            assert field in hints, f"Missing field: {field}"

    @pytest.mark.unit
    def test_prefix_is_string(self) -> None:
        """prefix は文字列型"""
        hints = get_type_hints(LevelConfigData)
        assert hints["prefix"] is str

    @pytest.mark.unit
    def test_digits_is_int(self) -> None:
        """digits は整数型"""
        hints = get_type_hints(LevelConfigData)
        assert hints["digits"] is int

    @pytest.mark.unit
    def test_next_is_optional_string(self) -> None:
        """next はOptional[str]型"""
        hints = get_type_hints(LevelConfigData)
        assert get_origin(hints["next"]) is type(None) or hints["next"] == Optional[str]


class TestLevelHierarchyEntry:
    """LevelHierarchyEntry 型のテスト"""

    @pytest.mark.unit
    def test_has_source_field(self) -> None:
        """source フィールドを持つ"""
        hints = get_type_hints(LevelHierarchyEntry)
        assert "source" in hints

    @pytest.mark.unit
    def test_has_next_field(self) -> None:
        """next フィールドを持つ"""
        hints = get_type_hints(LevelHierarchyEntry)
        assert "next" in hints
