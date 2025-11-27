#!/usr/bin/env python3
"""
validators.py のユニットテスト
==============================

バリデーション関数の動作を検証。
- validate_dict, validate_list, validate_source_files
- is_valid_dict, is_valid_list
- get_dict_or_default, get_list_or_default
"""
import pytest

# Application層
from application.validators import (
    validate_dict,
    validate_list,
    validate_source_files,
    is_valid_dict,
    is_valid_list,
    get_dict_or_default,
    get_list_or_default,
)

# Domain層
from domain.exceptions import ValidationError


# =============================================================================
# validate_dict テスト
# =============================================================================

class TestValidateDict:
    """validate_dict 関数のテスト"""

    @pytest.mark.unit
    def test_with_valid_dict(self):
        """dictを渡すとそのまま返す"""
        data = {"key": "value"}
        result = validate_dict(data, "test context")
        assert result == data
        assert result is data  # 同一オブジェクト

    @pytest.mark.unit
    def test_with_empty_dict(self):
        """空のdictも有効"""
        data = {}
        result = validate_dict(data, "test context")
        assert result == {}

    @pytest.mark.unit
    def test_with_nested_dict(self):
        """ネストしたdictも有効"""
        data = {"outer": {"inner": "value"}}
        result = validate_dict(data, "test context")
        assert result == data

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_input,expected_type", [
        (["item"], "list"),
        ("string", "str"),
        (None, "NoneType"),
        (123, "int"),
        ((1, 2), "tuple"),
    ])
    def test_with_invalid_type_raises_error(self, invalid_input, expected_type):
        """dict以外の型を渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_dict(invalid_input, "test context")
        assert expected_type in str(exc_info.value)
        assert "expected dict" in str(exc_info.value)


# =============================================================================
# validate_list テスト
# =============================================================================

class TestValidateList:
    """validate_list 関数のテスト"""

    @pytest.mark.unit
    def test_with_valid_list(self):
        """listを渡すとそのまま返す"""
        data = ["item1", "item2"]
        result = validate_list(data, "test context")
        assert result == data
        assert result is data

    @pytest.mark.unit
    def test_with_empty_list(self):
        """空のlistも有効"""
        data = []
        result = validate_list(data, "test context")
        assert result == []

    @pytest.mark.unit
    def test_with_nested_list(self):
        """ネストしたlistも有効"""
        data = [[1, 2], [3, 4]]
        result = validate_list(data, "test context")
        assert result == data

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_input,expected_type", [
        ({"key": "value"}, "dict"),
        ("string", "str"),
        (None, "NoneType"),
        ((1, 2, 3), "tuple"),
        (123, "int"),
    ])
    def test_with_invalid_type_raises_error(self, invalid_input, expected_type):
        """list以外の型を渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list(invalid_input, "test context")
        assert expected_type in str(exc_info.value)
        assert "expected list" in str(exc_info.value)


# =============================================================================
# validate_source_files テスト
# =============================================================================

class TestValidateSourceFiles:
    """validate_source_files 関数のテスト"""

    @pytest.mark.unit
    def test_with_valid_files(self):
        """有効なファイルリストを渡すとそのまま返す"""
        files = ["Loop001.txt", "Loop002.txt"]
        result = validate_source_files(files)
        assert result == files

    @pytest.mark.unit
    def test_with_single_file(self):
        """1ファイルでも有効"""
        files = ["Loop001.txt"]
        result = validate_source_files(files)
        assert result == files

    @pytest.mark.unit
    def test_with_none_raises_error(self):
        """Noneを渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_source_files(None)
        assert "cannot be None" in str(exc_info.value)
        assert "source_files" in str(exc_info.value)

    @pytest.mark.unit
    def test_with_empty_list_raises_error(self):
        """空リストを渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_source_files([])
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.unit
    def test_with_dict_raises_error(self):
        """dictを渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_source_files({"file": "Loop001.txt"})
        assert "expected list" in str(exc_info.value)

    @pytest.mark.unit
    def test_with_string_raises_error(self):
        """文字列を渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_source_files("Loop001.txt")
        assert "expected list" in str(exc_info.value)

    @pytest.mark.unit
    def test_custom_context(self):
        """カスタムcontext文字列が使用される"""
        with pytest.raises(ValidationError) as exc_info:
            validate_source_files(None, "custom_context")
        assert "custom_context" in str(exc_info.value)

    @pytest.mark.unit
    def test_default_context(self):
        """デフォルトcontextは'source_files'"""
        with pytest.raises(ValidationError) as exc_info:
            validate_source_files(None)
        assert "source_files" in str(exc_info.value)


# =============================================================================
# is_valid_dict テスト
# =============================================================================

class TestIsValidDict:
    """is_valid_dict 関数のテスト"""

    @pytest.mark.unit
    def test_with_dict_returns_true(self):
        """dictを渡すとTrue"""
        assert is_valid_dict({"key": "value"}) is True

    @pytest.mark.unit
    def test_with_empty_dict_returns_true(self):
        """空dictを渡すとTrue"""
        assert is_valid_dict({}) is True

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_input", [
        [1, 2, 3],
        None,
        "string",
        123,
        (1, 2),
        3.14,
    ])
    def test_with_non_dict_returns_false(self, invalid_input):
        """dict以外を渡すとFalse"""
        assert is_valid_dict(invalid_input) is False


# =============================================================================
# is_valid_list テスト
# =============================================================================

class TestIsValidList:
    """is_valid_list 関数のテスト"""

    @pytest.mark.unit
    def test_with_list_returns_true(self):
        """listを渡すとTrue"""
        assert is_valid_list([1, 2, 3]) is True

    @pytest.mark.unit
    def test_with_empty_list_returns_true(self):
        """空listを渡すとTrue"""
        assert is_valid_list([]) is True

    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_input", [
        {"key": "value"},
        None,
        (1, 2, 3),
        "string",
        123,
        3.14,
    ])
    def test_with_non_list_returns_false(self, invalid_input):
        """list以外を渡すとFalse"""
        assert is_valid_list(invalid_input) is False


# =============================================================================
# get_dict_or_default テスト
# =============================================================================

class TestGetDictOrDefault:
    """get_dict_or_default 関数のテスト"""

    @pytest.mark.unit
    def test_with_dict_returns_dict(self):
        """dictを渡すとそのまま返す"""
        data = {"key": "value"}
        result = get_dict_or_default(data)
        assert result == data
        assert result is data

    @pytest.mark.unit
    def test_with_non_dict_returns_empty_dict(self):
        """dict以外を渡すと空dictを返す"""
        result = get_dict_or_default("not a dict")
        assert result == {}

    @pytest.mark.unit
    def test_with_none_returns_empty_dict(self):
        """Noneを渡すと空dictを返す"""
        result = get_dict_or_default(None)
        assert result == {}

    @pytest.mark.unit
    def test_with_custom_default(self):
        """カスタムデフォルト値が使用される"""
        default = {"default": "value"}
        result = get_dict_or_default("not a dict", default)
        assert result == default
        assert result is default

    @pytest.mark.unit
    def test_with_none_and_custom_default(self):
        """None + カスタムデフォルト"""
        default = {"default": "value"}
        result = get_dict_or_default(None, default)
        assert result == default

    @pytest.mark.unit
    def test_with_list_returns_default(self):
        """listを渡すとデフォルトを返す"""
        result = get_dict_or_default([1, 2, 3])
        assert result == {}

    @pytest.mark.unit
    def test_default_none_becomes_empty_dict(self):
        """default=Noneの場合も空dictを返す"""
        result = get_dict_or_default("not a dict", None)
        assert result == {}


# =============================================================================
# get_list_or_default テスト
# =============================================================================

class TestGetListOrDefault:
    """get_list_or_default 関数のテスト"""

    @pytest.mark.unit
    def test_with_list_returns_list(self):
        """listを渡すとそのまま返す"""
        data = [1, 2, 3]
        result = get_list_or_default(data)
        assert result == data
        assert result is data

    @pytest.mark.unit
    def test_with_non_list_returns_empty_list(self):
        """list以外を渡すと空listを返す"""
        result = get_list_or_default("not a list")
        assert result == []

    @pytest.mark.unit
    def test_with_none_returns_empty_list(self):
        """Noneを渡すと空listを返す"""
        result = get_list_or_default(None)
        assert result == []

    @pytest.mark.unit
    def test_with_custom_default(self):
        """カスタムデフォルト値が使用される"""
        default = ["default", "value"]
        result = get_list_or_default("not a list", default)
        assert result == default
        assert result is default

    @pytest.mark.unit
    def test_with_none_and_custom_default(self):
        """None + カスタムデフォルト"""
        default = ["default"]
        result = get_list_or_default(None, default)
        assert result == default

    @pytest.mark.unit
    def test_with_dict_returns_default(self):
        """dictを渡すとデフォルトを返す"""
        result = get_list_or_default({"key": "value"})
        assert result == []

    @pytest.mark.unit
    def test_with_tuple_returns_default(self):
        """tupleを渡すとデフォルトを返す（tupleはlistではない）"""
        result = get_list_or_default((1, 2, 3))
        assert result == []

    @pytest.mark.unit
    def test_default_none_becomes_empty_list(self):
        """default=Noneの場合も空listを返す"""
        result = get_list_or_default("not a list", None)
        assert result == []
