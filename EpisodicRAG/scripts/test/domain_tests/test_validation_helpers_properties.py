#!/usr/bin/env python3
"""
Property-Based Tests for Validation Helpers
============================================

Using hypothesis to test invariants in domain/validators/helpers.py
"""

from typing import Any, List

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from domain.exceptions import ValidationError
from domain.validators.helpers import (
    collect_list_element_errors,
    collect_type_error,
    validate_dict_has_keys,
    validate_dict_key_type,
    validate_list_not_empty,
    validate_type,
)

# =============================================================================
# Strategies for generating test data
# =============================================================================

# Valid non-empty lists
non_empty_lists = st.lists(st.text(min_size=1), min_size=1, max_size=20)

# Valid dictionaries with string keys
valid_dicts = st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.one_of(st.integers(), st.text(), st.booleans()),
    min_size=1,
    max_size=10,
)

# Non-list values
non_list_values = st.one_of(
    st.none(),
    st.integers(),
    st.text(),
    st.dictionaries(st.text(), st.integers()),
)

# Non-dict values
non_dict_values = st.one_of(
    st.none(),
    st.integers(),
    st.text(),
    st.lists(st.integers()),
)


# =============================================================================
# validate_list_not_empty Properties
# =============================================================================


class TestValidateListNotEmptyProperties:
    """Property-based tests for validate_list_not_empty"""

    @pytest.mark.property
    @given(lst=non_empty_lists)
    @settings(max_examples=200)
    def test_passes_for_non_empty_list(self, lst) -> None:
        """非空リストは検証を通過し、同じリストを返す"""
        result = validate_list_not_empty(lst, "test_context")
        assert result is lst

    @pytest.mark.property
    @given(data=non_list_values)
    @settings(max_examples=100)
    def test_raises_for_non_list(self, data) -> None:
        """list以外の入力はValidationErrorを発生"""
        with pytest.raises(ValidationError):
            validate_list_not_empty(data, "test_context")

    @pytest.mark.property
    def test_raises_for_empty_list(self) -> None:
        """空リストはValidationErrorを発生"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list_not_empty([], "empty_test")
        # "cannot be empty" または "empty" がメッセージに含まれる
        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.property
    def test_raises_for_none(self) -> None:
        """NoneはValidationErrorを発生"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list_not_empty(None, "none_test")
        assert "None" in str(exc_info.value)


# =============================================================================
# validate_dict_has_keys Properties
# =============================================================================


class TestValidateDictHasKeysProperties:
    """Property-based tests for validate_dict_has_keys"""

    @pytest.mark.property
    @given(keys=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5, unique=True))
    @settings(max_examples=200)
    def test_passes_when_all_keys_present(self, keys) -> None:
        """全必須キーが存在すれば検証通過（例外なし）"""
        data = {k: f"value_{i}" for i, k in enumerate(keys)}
        # 例外が発生しないことを確認
        validate_dict_has_keys(data, keys, "test_context")

    @pytest.mark.property
    @given(
        present_keys=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3, unique=True),
        missing_key=st.text(min_size=1, max_size=10),
    )
    @settings(max_examples=100)
    def test_raises_when_key_missing(self, present_keys, missing_key) -> None:
        """必須キーが存在しなければValidationError"""
        # missing_keyがpresent_keysに含まれていないことを保証
        assume(missing_key not in present_keys)

        data = {k: f"value_{i}" for i, k in enumerate(present_keys)}
        required_keys = present_keys + [missing_key]

        with pytest.raises(ValidationError) as exc_info:
            validate_dict_has_keys(data, required_keys, "test_context")
        assert missing_key in str(exc_info.value)

    @pytest.mark.property
    @given(keys=st.lists(st.text(min_size=1), min_size=0, max_size=5, unique=True))
    @settings(max_examples=50)
    def test_empty_required_keys_always_passes(self, keys) -> None:
        """必須キーが空なら常に通過"""
        data = {k: f"value_{i}" for i, k in enumerate(keys)}
        # 空の必須キーリストなら例外なし
        validate_dict_has_keys(data, [], "test_context")


# =============================================================================
# validate_dict_key_type Properties
# =============================================================================


class TestValidateDictKeyTypeProperties:
    """Property-based tests for validate_dict_key_type"""

    @pytest.mark.property
    @given(key=st.text(min_size=1, max_size=10), value=st.text(min_size=1))
    @settings(max_examples=200)
    def test_returns_value_when_type_matches_str(self, key, value) -> None:
        """型が一致すれば値を返す（str）"""
        data = {key: value}
        result = validate_dict_key_type(data, key, str, "test_context")
        assert result == value

    @pytest.mark.property
    @given(key=st.text(min_size=1, max_size=10), value=st.integers())
    @settings(max_examples=200)
    def test_returns_value_when_type_matches_int(self, key, value) -> None:
        """型が一致すれば値を返す（int）"""
        data = {key: value}
        result = validate_dict_key_type(data, key, int, "test_context")
        assert result == value

    @pytest.mark.property
    @given(key=st.text(min_size=1, max_size=10), value=st.integers())
    @settings(max_examples=100)
    def test_raises_when_type_mismatch(self, key, value) -> None:
        """型が一致しなければValidationError"""
        data = {key: value}  # int value
        with pytest.raises(ValidationError):
            validate_dict_key_type(data, key, str, "test_context")  # expects str

    @pytest.mark.property
    @given(
        present_key=st.text(min_size=1, max_size=10),
        missing_key=st.text(min_size=1, max_size=10),
    )
    @settings(max_examples=100)
    def test_raises_when_key_missing(self, present_key, missing_key) -> None:
        """キーが存在しなければValidationError"""
        assume(present_key != missing_key)
        data = {present_key: "value"}
        with pytest.raises(ValidationError) as exc_info:
            validate_dict_key_type(data, missing_key, str, "test_context")
        assert missing_key in str(exc_info.value)


# =============================================================================
# collect_list_element_errors Properties
# =============================================================================


class TestCollectListElementErrorsProperties:
    """Property-based tests for collect_list_element_errors"""

    @pytest.mark.property
    @given(lst=st.lists(st.integers(), min_size=0, max_size=20))
    @settings(max_examples=200)
    def test_no_errors_when_all_types_match(self, lst) -> None:
        """全要素が期待型なら空のエラーリスト"""
        errors: List[str] = []
        collect_list_element_errors(lst, int, "items", errors)
        assert errors == []

    @pytest.mark.property
    @given(lst=st.lists(st.text(), min_size=0, max_size=20))
    @settings(max_examples=200)
    def test_no_errors_when_all_strings(self, lst) -> None:
        """全要素がstrなら空のエラーリスト"""
        errors: List[str] = []
        collect_list_element_errors(lst, str, "items", errors)
        assert errors == []

    @pytest.mark.property
    @given(
        valid_count=st.integers(min_value=0, max_value=10),
        invalid_count=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=200)
    def test_error_count_matches_invalid_count(self, valid_count, invalid_count) -> None:
        """エラー数 == 型が一致しない要素数"""
        lst: List[Any] = [1] * valid_count + ["str"] * invalid_count
        errors: List[str] = []
        collect_list_element_errors(lst, int, "items", errors)
        assert len(errors) == invalid_count

    @pytest.mark.property
    @given(existing_errors=st.lists(st.text(min_size=1), min_size=1, max_size=5))
    @settings(max_examples=100)
    def test_preserves_existing_errors(self, existing_errors) -> None:
        """既存のエラーを保持しつつ追加"""
        errors = existing_errors.copy()
        original_count = len(errors)

        # 型不一致の要素を追加
        lst = ["string", 123]  # expects int
        collect_list_element_errors(lst, int, "items", errors)

        # 既存エラー + 新規エラー1件
        assert len(errors) == original_count + 1
        # 既存エラーが先頭に残っている
        for i, original in enumerate(existing_errors):
            assert errors[i] == original


# =============================================================================
# collect_type_error Properties
# =============================================================================


class TestCollectTypeErrorProperties:
    """Property-based tests for collect_type_error"""

    @pytest.mark.property
    @given(value=st.integers())
    @settings(max_examples=100)
    def test_no_error_when_type_matches(self, value) -> None:
        """型が一致すればエラーリストは空のまま"""
        errors: List[str] = []
        collect_type_error(value, int, "test_key", errors)
        assert errors == []

    @pytest.mark.property
    @given(value=st.text())
    @settings(max_examples=100)
    def test_adds_error_when_type_mismatch(self, value) -> None:
        """型が不一致ならエラーを追加"""
        errors: List[str] = []
        collect_type_error(value, int, "test_key", errors)
        assert len(errors) == 1
        assert "test_key" in errors[0]
        assert "int" in errors[0]
        assert "str" in errors[0]


# =============================================================================
# validate_type Properties
# =============================================================================


class TestValidateTypeProperties:
    """Property-based tests for validate_type"""

    @pytest.mark.property
    @given(value=st.integers())
    @settings(max_examples=100)
    def test_returns_same_value_when_type_matches(self, value) -> None:
        """型が一致すれば同じ値を返す"""
        result = validate_type(value, int, "test_context", "int")
        assert result == value

    @pytest.mark.property
    @given(value=st.text())
    @settings(max_examples=100)
    def test_raises_when_type_mismatch(self, value) -> None:
        """型が不一致ならValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_type(value, int, "test_context", "int")
        assert "int" in str(exc_info.value)
        assert "str" in str(exc_info.value)
