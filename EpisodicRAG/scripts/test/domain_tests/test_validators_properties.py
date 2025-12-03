#!/usr/bin/env python3
"""
Property-Based Tests for Validators
====================================

Using hypothesis to test type validation invariants.
"""

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from application.validators import (
    get_dict_or_default,
    get_list_or_default,
    is_valid_dict,
    is_valid_list,
    validate_dict,
    validate_list,
    validate_source_files,
)
from domain.exceptions import ValidationError

# =============================================================================
# Strategies
# =============================================================================

# Any value that is NOT a dict
non_dict_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.binary(),
)

# Any value that is NOT a list
non_list_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False),
    st.text(),
    st.dictionaries(st.text(), st.integers()),
    st.tuples(st.integers()),
    st.binary(),
)

# Valid dicts (any structure)
valid_dicts = st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.one_of(st.integers(), st.text(), st.booleans()),
    max_size=10,
)

# Valid lists (any structure)
valid_lists = st.lists(st.one_of(st.integers(), st.text(), st.booleans()), max_size=20)

# Non-empty lists of strings (valid source files)
valid_source_files = st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=20)


# =============================================================================
# validate_dict Properties
# =============================================================================


class TestValidateDictProperties:
    """Property-based tests for validate_dict"""

    @pytest.mark.property
    @given(data=valid_dicts)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_returns_same_dict_when_valid(self, data) -> None:

        """validate_dict returns the exact same dict object when valid"""
        result = validate_dict(data, "test")
        assert result is data

    @pytest.mark.property
    @given(data=non_dict_values)
    @settings(max_examples=200)
    def test_raises_for_non_dict(self, data) -> None:

        """validate_dict raises ValidationError for any non-dict input"""
        with pytest.raises(ValidationError) as exc_info:
            validate_dict(data, "test context")
        assert "expected dict" in str(exc_info.value)


# =============================================================================
# validate_list Properties
# =============================================================================


class TestValidateListProperties:
    """Property-based tests for validate_list"""

    @pytest.mark.property
    @given(data=valid_lists)
    @settings(max_examples=200)
    def test_returns_same_list_when_valid(self, data) -> None:

        """validate_list returns the exact same list object when valid"""
        result = validate_list(data, "test")
        assert result is data

    @pytest.mark.property
    @given(data=non_list_values)
    @settings(max_examples=200)
    def test_raises_for_non_list(self, data) -> None:

        """validate_list raises ValidationError for any non-list input"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list(data, "test context")
        assert "expected list" in str(exc_info.value)


# =============================================================================
# is_valid_dict / is_valid_list Properties
# =============================================================================


class TestIsValidProperties:
    """Property-based tests for is_valid_* functions"""

    @pytest.mark.property
    @given(data=valid_dicts)
    @settings(max_examples=100)
    def test_is_valid_dict_true_for_dicts(self, data) -> None:

        """is_valid_dict returns True for any dict"""
        assert is_valid_dict(data) is True

    @pytest.mark.property
    @given(data=non_dict_values)
    @settings(max_examples=100)
    def test_is_valid_dict_false_for_non_dicts(self, data) -> None:

        """is_valid_dict returns False for any non-dict"""
        assert is_valid_dict(data) is False

    @pytest.mark.property
    @given(data=valid_lists)
    @settings(max_examples=100)
    def test_is_valid_list_true_for_lists(self, data) -> None:

        """is_valid_list returns True for any list"""
        assert is_valid_list(data) is True

    @pytest.mark.property
    @given(data=non_list_values)
    @settings(max_examples=100)
    def test_is_valid_list_false_for_non_lists(self, data) -> None:

        """is_valid_list returns False for any non-list"""
        assert is_valid_list(data) is False


# =============================================================================
# get_dict_or_default / get_list_or_default Properties
# =============================================================================


class TestGetOrDefaultProperties:
    """Property-based tests for get_*_or_default functions"""

    @pytest.mark.property
    @given(data=valid_dicts)
    @settings(max_examples=100)
    def test_get_dict_returns_input_when_valid(self, data) -> None:

        """get_dict_or_default returns input when it's a valid dict"""
        result = get_dict_or_default(data, {"default": True})
        assert result is data

    @pytest.mark.property
    @given(data=non_dict_values, default=valid_dicts)
    @settings(max_examples=100)
    def test_get_dict_returns_default_when_invalid(self, data, default) -> None:

        """get_dict_or_default returns default when input is not a dict"""
        result = get_dict_or_default(data, default)
        assert result is default

    @pytest.mark.property
    @given(data=st.one_of(valid_dicts, non_dict_values))
    @settings(max_examples=100)
    def test_get_dict_never_raises(self, data) -> None:

        """get_dict_or_default never raises an exception"""
        # Should not raise
        result = get_dict_or_default(data)
        assert isinstance(result, dict)

    @pytest.mark.property
    @given(data=valid_lists)
    @settings(max_examples=100)
    def test_get_list_returns_input_when_valid(self, data) -> None:

        """get_list_or_default returns input when it's a valid list"""
        result = get_list_or_default(data, ["default"])
        assert result is data

    @pytest.mark.property
    @given(data=non_list_values, default=valid_lists)
    @settings(max_examples=100)
    def test_get_list_returns_default_when_invalid(self, data, default) -> None:

        """get_list_or_default returns default when input is not a list"""
        result = get_list_or_default(data, default)
        assert result is default

    @pytest.mark.property
    @given(data=st.one_of(valid_lists, non_list_values))
    @settings(max_examples=100)
    def test_get_list_never_raises(self, data) -> None:

        """get_list_or_default never raises an exception"""
        result = get_list_or_default(data)
        assert isinstance(result, list)


# =============================================================================
# validate_source_files Properties
# =============================================================================


class TestValidateSourceFilesProperties:
    """Property-based tests for validate_source_files"""

    @pytest.mark.property
    @given(files=valid_source_files)
    @settings(max_examples=100)
    def test_returns_same_list_when_valid(self, files) -> None:

        """validate_source_files returns exact same list when valid"""
        result = validate_source_files(files)
        assert result is files

    @pytest.mark.property
    @given(data=non_list_values)
    @settings(max_examples=100)
    def test_raises_for_non_list(self, data) -> None:

        """validate_source_files raises for any non-list input"""
        with pytest.raises(ValidationError):
            validate_source_files(data)

    @pytest.mark.property
    def test_raises_for_empty_list(self) -> None:

        """validate_source_files raises for empty list"""
        with pytest.raises(ValidationError) as exc_info:
            validate_source_files([])
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.property
    def test_raises_for_none(self) -> None:

        """validate_source_files raises for None"""
        with pytest.raises(ValidationError) as exc_info:
            validate_source_files(None)
        assert "cannot be None" in str(exc_info.value)
