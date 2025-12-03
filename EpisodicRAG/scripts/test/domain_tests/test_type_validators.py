#!/usr/bin/env python3
"""
test_type_validators.py
=======================

domain/validators/type_validators.py のユニットテスト。
型検証ユーティリティ関数の動作を検証。
"""

from typing import Any, Dict, List

import pytest

from domain.validators.type_validators import (
    get_dict_or_empty,
    get_list_or_empty,
    get_or_default,
    get_str_or_empty,
    is_valid_dict,
    is_valid_int,
    is_valid_list,
    is_valid_str,
    is_valid_type,
)

# =============================================================================
# is_valid_type テスト
# =============================================================================


class TestIsValidType:
    """is_valid_type 関数のテスト"""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "data,expected_type,expected_result",
        [
            ({"key": "value"}, dict, True),
            ([1, 2, 3], list, True),
            ("hello", str, True),
            (42, int, True),
            (3.14, float, True),
            (True, bool, True),
            (None, type(None), True),
        ],
    )
    def test_valid_types_return_true(self, data, expected_type, expected_result) -> None:
        """正しい型の場合 True を返す"""
        assert is_valid_type(data, expected_type) is expected_result

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "data,expected_type",
        [
            ({"key": "value"}, list),
            ([1, 2, 3], dict),
            ("hello", int),
            (42, str),
            (None, dict),
        ],
    )
    def test_invalid_types_return_false(self, data, expected_type) -> None:
        """異なる型の場合 False を返す"""
        assert is_valid_type(data, expected_type) is False

    @pytest.mark.unit
    def test_subclass_returns_true(self) -> None:
        """サブクラスは True（isinstance の挙動）"""
        # bool は int のサブクラス
        assert is_valid_type(True, int) is True


# =============================================================================
# get_or_default テスト
# =============================================================================


class TestGetOrDefault:
    """get_or_default 関数のテスト"""

    @pytest.mark.unit
    def test_returns_data_when_correct_type(self) -> None:
        """正しい型の場合はデータをそのまま返す"""
        data = {"key": "value"}
        result = get_or_default(data, dict, dict)
        assert result == data
        assert result is data  # 同一オブジェクト

    @pytest.mark.unit
    def test_returns_default_when_wrong_type(self) -> None:
        """異なる型の場合はデフォルトを返す"""
        data = "not a dict"
        result = get_or_default(data, dict, dict)
        assert result == {}

    @pytest.mark.unit
    def test_returns_default_when_none(self) -> None:
        """None の場合はデフォルトを返す"""
        result = get_or_default(None, dict, dict)
        assert result == {}

    @pytest.mark.unit
    def test_custom_default_factory(self) -> None:
        """カスタムデフォルトファクトリが使用される"""
        result = get_or_default(None, list, lambda: [1, 2, 3])
        assert result == [1, 2, 3]

    @pytest.mark.unit
    def test_factory_called_on_wrong_type(self):
        """異なる型の場合にファクトリが呼ばれる"""
        call_count = [0]

        def counting_factory():
            call_count[0] += 1
            return {}

        get_or_default("wrong type", dict, counting_factory)
        assert call_count[0] == 1

    @pytest.mark.unit
    def test_factory_not_called_on_correct_type(self):
        """正しい型の場合はファクトリは呼ばれない"""
        call_count = [0]

        def counting_factory():
            call_count[0] += 1
            return {}

        get_or_default({"correct": "type"}, dict, counting_factory)
        assert call_count[0] == 0


# =============================================================================
# is_valid_dict テスト (TypeGuard)
# =============================================================================


class TestIsValidDict:
    """is_valid_dict 関数のテスト"""

    @pytest.mark.unit
    def test_dict_returns_true(self) -> None:
        """dict は True"""
        assert is_valid_dict({"key": "value"}) is True

    @pytest.mark.unit
    def test_empty_dict_returns_true(self) -> None:
        """空 dict は True"""
        assert is_valid_dict({}) is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "non_dict_value",
        [
            [1, 2, 3],
            "string",
            42,
            None,
            (1, 2),
            {1, 2, 3},  # set
        ],
    )
    def test_non_dict_returns_false(self, non_dict_value) -> None:
        """dict 以外は False"""
        assert is_valid_dict(non_dict_value) is False

    @pytest.mark.unit
    def test_typeguard_narrows_type(self) -> None:
        """TypeGuard により型が絞り込まれる"""
        data: Any = {"key": "value"}
        if is_valid_dict(data):
            # この時点で data は Dict[str, Any] として扱える
            keys = data.keys()
            assert "key" in keys


# =============================================================================
# is_valid_list テスト (TypeGuard)
# =============================================================================


class TestIsValidList:
    """is_valid_list 関数のテスト"""

    @pytest.mark.unit
    def test_list_returns_true(self) -> None:
        """list は True"""
        assert is_valid_list([1, 2, 3]) is True

    @pytest.mark.unit
    def test_empty_list_returns_true(self) -> None:
        """空 list は True"""
        assert is_valid_list([]) is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "non_list_value",
        [
            {"key": "value"},
            "string",
            42,
            None,
            (1, 2, 3),  # tuple
        ],
    )
    def test_non_list_returns_false(self, non_list_value) -> None:
        """list 以外は False"""
        assert is_valid_list(non_list_value) is False


# =============================================================================
# is_valid_str テスト (TypeGuard)
# =============================================================================


class TestIsValidStr:
    """is_valid_str 関数のテスト"""

    @pytest.mark.unit
    def test_str_returns_true(self) -> None:
        """str は True"""
        assert is_valid_str("hello") is True

    @pytest.mark.unit
    def test_empty_str_returns_true(self) -> None:
        """空文字列は True"""
        assert is_valid_str("") is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "non_str_value",
        [
            {"key": "value"},
            [1, 2, 3],
            42,
            None,
            b"bytes",
        ],
    )
    def test_non_str_returns_false(self, non_str_value) -> None:
        """str 以外は False"""
        assert is_valid_str(non_str_value) is False


# =============================================================================
# is_valid_int テスト (TypeGuard)
# =============================================================================


class TestIsValidInt:
    """is_valid_int 関数のテスト"""

    @pytest.mark.unit
    def test_int_returns_true(self) -> None:
        """int は True"""
        assert is_valid_int(42) is True

    @pytest.mark.unit
    def test_zero_returns_true(self) -> None:
        """0 は True"""
        assert is_valid_int(0) is True

    @pytest.mark.unit
    def test_negative_int_returns_true(self) -> None:
        """負の整数は True"""
        assert is_valid_int(-10) is True

    @pytest.mark.unit
    def test_bool_returns_true(self) -> None:
        """bool は int のサブクラスなので True"""
        # Python では bool は int のサブクラス
        assert is_valid_int(True) is True
        assert is_valid_int(False) is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "non_int_value",
        [
            3.14,
            "42",
            None,
            [1, 2],
        ],
    )
    def test_non_int_returns_false(self, non_int_value) -> None:
        """int 以外は False"""
        assert is_valid_int(non_int_value) is False


# =============================================================================
# get_dict_or_empty テスト
# =============================================================================


class TestGetDictOrEmpty:
    """get_dict_or_empty 関数のテスト"""

    @pytest.mark.unit
    def test_dict_returns_same_dict(self) -> None:
        """dict を渡すとそのまま返す"""
        data = {"key": "value"}
        result = get_dict_or_empty(data)
        assert result == data
        assert result is data

    @pytest.mark.unit
    def test_non_dict_returns_empty_dict(self) -> None:
        """dict 以外を渡すと空 dict を返す"""
        assert get_dict_or_empty("not dict") == {}
        assert get_dict_or_empty([1, 2, 3]) == {}
        assert get_dict_or_empty(None) == {}

    @pytest.mark.unit
    def test_empty_dict_returns_empty_dict(self) -> None:
        """空 dict を渡すと空 dict を返す"""
        result = get_dict_or_empty({})
        assert result == {}


# =============================================================================
# get_list_or_empty テスト
# =============================================================================


class TestGetListOrEmpty:
    """get_list_or_empty 関数のテスト"""

    @pytest.mark.unit
    def test_list_returns_same_list(self) -> None:
        """list を渡すとそのまま返す"""
        data = [1, 2, 3]
        result = get_list_or_empty(data)
        assert result == data
        assert result is data

    @pytest.mark.unit
    def test_non_list_returns_empty_list(self) -> None:
        """list 以外を渡すと空 list を返す"""
        assert get_list_or_empty("not list") == []
        assert get_list_or_empty({"key": "value"}) == []
        assert get_list_or_empty(None) == []

    @pytest.mark.unit
    def test_tuple_returns_empty_list(self) -> None:
        """tuple を渡すと空 list を返す（tuple は list ではない）"""
        assert get_list_or_empty((1, 2, 3)) == []


# =============================================================================
# get_str_or_empty テスト
# =============================================================================


class TestGetStrOrEmpty:
    """get_str_or_empty 関数のテスト"""

    @pytest.mark.unit
    def test_str_returns_same_str(self) -> None:
        """str を渡すとそのまま返す"""
        data = "hello"
        result = get_str_or_empty(data)
        assert result == data
        assert result is data

    @pytest.mark.unit
    def test_non_str_returns_empty_str(self) -> None:
        """str 以外を渡すと空文字列を返す"""
        assert get_str_or_empty(42) == ""
        assert get_str_or_empty([1, 2, 3]) == ""
        assert get_str_or_empty(None) == ""

    @pytest.mark.unit
    def test_empty_str_returns_empty_str(self) -> None:
        """空文字列を渡すと空文字列を返す"""
        result = get_str_or_empty("")
        assert result == ""
