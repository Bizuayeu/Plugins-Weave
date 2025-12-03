#!/usr/bin/env python3
"""
Level Metadata Unit Tests
=========================

Tests for domain/level_metadata.py

Immutable dataclass for level properties.
"""

import pytest

from domain.level_metadata import LevelMetadata

# =============================================================================
# LevelMetadata Initialization Tests
# =============================================================================


class TestLevelMetadataInit:
    """LevelMetadata initialization tests"""

    def test_init_with_all_fields(self) -> None:

        """Initializes with all fields"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        assert metadata.name == "weekly"
        assert metadata.prefix == "W"
        assert metadata.digits == 4
        assert metadata.dir == "1_Weekly"
        assert metadata.source == "loops"
        assert metadata.next_level == "monthly"

    def test_init_with_none_next_level(self) -> None:

        """Initializes with None next_level (top level)"""
        metadata = LevelMetadata(
            name="centurial",
            prefix="C",
            digits=4,
            dir="8_Centurial",
            source="multi_decadal",
            next_level=None,
        )

        assert metadata.next_level is None

    def test_requires_all_positional_args(self) -> None:

        """Requires all positional arguments"""
        with pytest.raises(TypeError):
            LevelMetadata(name="weekly")  # Missing other args


# =============================================================================
# Immutability Tests (frozen=True)
# =============================================================================


class TestLevelMetadataImmutability:
    """LevelMetadata immutability tests"""

    @pytest.fixture
    def metadata(self):

        """Sample metadata"""
        return LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

    def test_cannot_modify_name(self, metadata) -> None:

        """Cannot modify name after creation"""
        with pytest.raises(AttributeError):
            metadata.name = "modified"

    def test_cannot_modify_prefix(self, metadata) -> None:

        """Cannot modify prefix after creation"""
        with pytest.raises(AttributeError):
            metadata.prefix = "X"

    def test_cannot_modify_digits(self, metadata) -> None:

        """Cannot modify digits after creation"""
        with pytest.raises(AttributeError):
            metadata.digits = 5

    def test_cannot_modify_dir(self, metadata) -> None:

        """Cannot modify dir after creation"""
        with pytest.raises(AttributeError):
            metadata.dir = "new_dir"

    def test_cannot_modify_source(self, metadata) -> None:

        """Cannot modify source after creation"""
        with pytest.raises(AttributeError):
            metadata.source = "different_source"

    def test_cannot_modify_next_level(self, metadata) -> None:

        """Cannot modify next_level after creation"""
        with pytest.raises(AttributeError):
            metadata.next_level = "quarterly"

    def test_cannot_delete_attribute(self, metadata) -> None:

        """Cannot delete attributes"""
        with pytest.raises(AttributeError):
            del metadata.name


# =============================================================================
# Equality Tests
# =============================================================================


class TestLevelMetadataEquality:
    """LevelMetadata equality tests"""

    def test_equal_metadata_are_equal(self) -> None:

        """Equal metadata instances are equal"""
        meta1 = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        meta2 = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        assert meta1 == meta2

    def test_different_name_not_equal(self) -> None:

        """Different names are not equal"""
        meta1 = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        meta2 = LevelMetadata(
            name="monthly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        assert meta1 != meta2

    def test_different_next_level_not_equal(self) -> None:

        """Different next_level are not equal"""
        meta1 = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        meta2 = LevelMetadata(
            name="weekly", prefix="W", digits=4, dir="1_Weekly", source="loops", next_level=None
        )

        assert meta1 != meta2


# =============================================================================
# Hashability Tests (frozen dataclass is hashable)
# =============================================================================


class TestLevelMetadataHashability:
    """LevelMetadata hashability tests"""

    def test_is_hashable(self) -> None:

        """Metadata is hashable"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        # Should not raise
        hash_value = hash(metadata)
        assert isinstance(hash_value, int)

    def test_can_be_used_in_set(self) -> None:

        """Can be used in set"""
        meta1 = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        meta2 = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        meta3 = LevelMetadata(
            name="monthly", prefix="M", digits=4, dir="2_Monthly", source="weekly", next_level=None
        )

        metadata_set = {meta1, meta2, meta3}

        # meta1 and meta2 are equal, so set should have 2 items
        assert len(metadata_set) == 2

    def test_can_be_used_as_dict_key(self) -> None:

        """Can be used as dictionary key"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        data = {metadata: "test_value"}

        assert data[metadata] == "test_value"


# =============================================================================
# All Level Types Tests
# =============================================================================


class TestAllLevelTypes:
    """Tests for all 8 level types"""

    @pytest.mark.parametrize(
        "name,prefix,source,next_level",
        [
            ("weekly", "W", "loops", "monthly"),
            ("monthly", "M", "weekly", "quarterly"),
            ("quarterly", "Q", "monthly", "annual"),
            ("annual", "A", "quarterly", "triennial"),
            ("triennial", "T", "annual", "decadal"),
            ("decadal", "D", "triennial", "multi_decadal"),
            ("multi_decadal", "MD", "decadal", "centurial"),
            ("centurial", "C", "multi_decadal", None),
        ],
    )
    def test_all_level_configurations(self, name, prefix, source, next_level) -> None:

        """All level configurations can be created"""
        metadata = LevelMetadata(
            name=name,
            prefix=prefix,
            digits=4,
            dir=f"x_{name}",
            source=source,
            next_level=next_level,
        )

        assert metadata.name == name
        assert metadata.prefix == prefix
        assert metadata.source == source
        assert metadata.next_level == next_level


# =============================================================================
# String Representation Tests
# =============================================================================


class TestLevelMetadataRepr:
    """String representation tests"""

    def test_repr_contains_class_name(self) -> None:

        """Repr contains class name"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        repr_str = repr(metadata)
        assert "LevelMetadata" in repr_str

    def test_repr_contains_field_values(self) -> None:

        """Repr contains field values"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        repr_str = repr(metadata)
        assert "weekly" in repr_str
        assert "W" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
