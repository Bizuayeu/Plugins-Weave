#!/usr/bin/env python3
"""
Property-Based Tests for Text Utils
====================================

Using hypothesis to test invariants in text_utils.py
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from domain.text_utils import extract_long_value, extract_short_value, extract_value

# =============================================================================
# Strategies for generating test data
# =============================================================================

# Valid LongShortText dictionaries
long_short_dicts = st.fixed_dictionaries({
    "long": st.text(min_size=1, max_size=100),
    "short": st.text(min_size=1, max_size=50),
})

# Arbitrary non-dict values
non_dict_values = st.one_of(
    st.none(),
    st.integers(),
    st.floats(allow_nan=False),
    st.lists(st.text()),
    st.tuples(st.text()),
)


# =============================================================================
# extract_long_value Properties
# =============================================================================


class TestExtractLongValueProperties:
    """Property-based tests for extract_long_value"""

    @pytest.mark.property
    @given(data=long_short_dicts)
    @settings(max_examples=200)
    def test_extract_long_returns_long_key(self, data) -> None:
        """LongShortTextからlongの値が正しく抽出される"""
        result = extract_long_value(data)
        assert result == data["long"]

    @pytest.mark.property
    @given(text=st.text(min_size=1))
    @settings(max_examples=200)
    def test_extract_long_from_string_returns_string(self, text) -> None:
        """非空文字列入力はそのまま返される"""
        result = extract_long_value(text)
        assert result == text

    @pytest.mark.property
    @given(data=non_dict_values)
    @settings(max_examples=100)
    def test_extract_long_from_non_dict_returns_default(self, data) -> None:
        """dict/str以外の入力にはdefaultを返す"""
        default = "fallback_value"
        result = extract_long_value(data, default)
        assert result == default

    @pytest.mark.property
    @given(default=st.text(min_size=1))
    @settings(max_examples=50)
    def test_extract_long_empty_string_returns_default(self, default) -> None:
        """空文字列入力はdefaultを返す"""
        result = extract_long_value("", default)
        assert result == default

    @pytest.mark.property
    @given(other_key=st.text(min_size=1).filter(lambda x: x != "long"))
    @settings(max_examples=100)
    def test_extract_long_missing_key_returns_default(self, other_key) -> None:
        """'long'キーがない辞書はdefaultを返す"""
        data = {other_key: "some_value"}
        default = "default_val"
        result = extract_long_value(data, default)
        assert result == default


# =============================================================================
# extract_short_value Properties
# =============================================================================


class TestExtractShortValueProperties:
    """Property-based tests for extract_short_value"""

    @pytest.mark.property
    @given(data=long_short_dicts)
    @settings(max_examples=200)
    def test_extract_short_returns_short_key(self, data) -> None:
        """LongShortTextからshortの値が正しく抽出される"""
        result = extract_short_value(data)
        assert result == data["short"]

    @pytest.mark.property
    @given(data=non_dict_values)
    @settings(max_examples=100)
    def test_extract_short_from_non_dict_returns_default(self, data) -> None:
        """dict以外の入力にはdefaultを返す"""
        default = "fallback_short"
        result = extract_short_value(data, default)
        assert result == default

    @pytest.mark.property
    @given(text=st.text())
    @settings(max_examples=100)
    def test_extract_short_from_string_returns_default(self, text) -> None:
        """文字列入力はdefaultを返す（shortは辞書専用）"""
        default = "default_short"
        result = extract_short_value(text, default)
        assert result == default

    @pytest.mark.property
    @given(other_key=st.text(min_size=1).filter(lambda x: x != "short"))
    @settings(max_examples=100)
    def test_extract_short_missing_key_returns_default(self, other_key) -> None:
        """'short'キーがない辞書はdefaultを返す"""
        data = {other_key: "some_value"}
        default = "default_val"
        result = extract_short_value(data, default)
        assert result == default


# =============================================================================
# extract_value Properties (Generic)
# =============================================================================


class TestExtractValueProperties:
    """Property-based tests for extract_value"""

    @pytest.mark.property
    @given(key=st.sampled_from(["long", "short"]), value=st.text(min_size=1))
    @settings(max_examples=200)
    def test_extract_value_returns_correct_key(self, key, value) -> None:
        """任意キーでの抽出が正しく動作"""
        data = {key: value}
        result = extract_value(data, key)
        assert result == value

    @pytest.mark.property
    @given(
        key=st.text(min_size=1, max_size=20),
        value=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=200)
    def test_extract_value_arbitrary_key(self, key, value) -> None:
        """任意のキー名で値を抽出できる"""
        data = {key: value}
        result = extract_value(data, key)
        assert result == value

    @pytest.mark.property
    @given(
        existing_key=st.text(min_size=1, max_size=10),
        missing_key=st.text(min_size=1, max_size=10),
        default=st.text(min_size=1),
    )
    @settings(max_examples=100)
    def test_extract_value_missing_key_returns_default(
        self, existing_key, missing_key, default
    ) -> None:
        """存在しないキーはdefaultを返す"""
        # existing_keyとmissing_keyが同じ場合はスキップ
        if existing_key == missing_key:
            return

        data = {existing_key: "value"}
        result = extract_value(data, missing_key, default)
        assert result == default

    @pytest.mark.property
    @given(data=non_dict_values, key=st.text(min_size=1))
    @settings(max_examples=100)
    def test_extract_value_from_non_dict_returns_default(self, data, key) -> None:
        """dict以外の入力にはdefaultを返す"""
        default = "non_dict_default"
        result = extract_value(data, key, default)
        assert result == default


# =============================================================================
# Consistency Properties
# =============================================================================


class TestTextUtilsConsistency:
    """Cross-function consistency tests"""

    @pytest.mark.property
    @given(data=long_short_dicts)
    @settings(max_examples=100)
    def test_extract_long_equals_extract_value_long(self, data) -> None:
        """extract_long_value == extract_value(..., 'long')"""
        long_result = extract_long_value(data)
        value_result = extract_value(data, "long")
        assert long_result == value_result

    @pytest.mark.property
    @given(data=long_short_dicts)
    @settings(max_examples=100)
    def test_extract_short_equals_extract_value_short(self, data) -> None:
        """extract_short_value == extract_value(..., 'short')"""
        short_result = extract_short_value(data)
        value_result = extract_value(data, "short")
        assert short_result == value_result
