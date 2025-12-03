#!/usr/bin/env python3
"""
domain/validation_helpers.py のユニットテスト
==============================================

統一バリデーションヘルパーのテスト。
- validate_list_not_empty
- validate_dict_has_keys
- validate_dict_key_type
- collect_list_element_errors
"""

import pytest

from domain.exceptions import ValidationError
from domain.validation_helpers import (
    collect_list_element_errors,
    validate_dict_has_keys,
    validate_dict_key_type,
    validate_list_not_empty,
)

# =============================================================================
# validate_list_not_empty テスト
# =============================================================================


class TestValidateListNotEmpty:
    """validate_list_not_empty 関数のテスト"""

    @pytest.mark.unit
    def test_valid_list_returns_list(self) -> None:
        """有効なリストをそのまま返す"""
        data = [1, 2, 3]
        result = validate_list_not_empty(data, "test_field")
        assert result == [1, 2, 3]
        assert result is data

    @pytest.mark.unit
    def test_single_element_list_is_valid(self) -> None:
        """単一要素のリストも有効"""
        result = validate_list_not_empty(["single"], "field")
        assert result == ["single"]

    @pytest.mark.unit
    def test_list_with_none_elements_is_valid(self) -> None:
        """Noneを含むリストも有効（リスト自体は空でない）"""
        result = validate_list_not_empty([None, None], "field")
        assert result == [None, None]

    @pytest.mark.unit
    def test_none_raises_validation_error(self) -> None:
        """Noneを渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list_not_empty(None, "source_files")

        assert "cannot be None" in str(exc_info.value)

    @pytest.mark.unit
    def test_empty_list_raises_validation_error(self) -> None:
        """空リストを渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list_not_empty([], "source_files")

        error_msg = str(exc_info.value)
        # empty_collection エラーメッセージを含む
        assert "source_files" in error_msg

    @pytest.mark.unit
    def test_non_list_raises_validation_error(self) -> None:
        """リスト以外を渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list_not_empty("not a list", "field")

        error_msg = str(exc_info.value)
        assert "expected list" in error_msg
        assert "got str" in error_msg

    @pytest.mark.unit
    def test_dict_raises_validation_error(self) -> None:
        """dictを渡すとValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list_not_empty({"key": "value"}, "field")

        assert "expected list" in str(exc_info.value)

    @pytest.mark.unit
    def test_int_raises_validation_error(self) -> None:
        """intを渡すとValidationError"""
        with pytest.raises(ValidationError):
            validate_list_not_empty(123, "field")

    @pytest.mark.unit
    def test_context_in_error_message(self) -> None:
        """エラーメッセージにコンテキストが含まれる"""
        with pytest.raises(ValidationError) as exc_info:
            validate_list_not_empty(None, "my_custom_context")

        assert "my_custom_context" in str(exc_info.value)


# =============================================================================
# validate_dict_has_keys テスト
# =============================================================================


class TestValidateDictHasKeys:
    """validate_dict_has_keys 関数のテスト"""

    @pytest.mark.unit
    def test_all_keys_present_succeeds(self) -> None:
        """すべてのキーが存在する場合は成功"""
        data = {"long": "hello", "short": "hi"}
        # 例外が発生しないことを確認
        validate_dict_has_keys(data, ["long", "short"], "abstract")

    @pytest.mark.unit
    def test_extra_keys_allowed(self) -> None:
        """追加のキーがあっても成功"""
        data = {"long": "hello", "short": "hi", "extra": "value"}
        validate_dict_has_keys(data, ["long", "short"], "field")

    @pytest.mark.unit
    def test_empty_required_keys_succeeds(self) -> None:
        """必須キーが空の場合は常に成功"""
        validate_dict_has_keys({"any": "value"}, [], "field")
        validate_dict_has_keys({}, [], "field")

    @pytest.mark.unit
    def test_missing_key_raises_validation_error(self) -> None:
        """必須キーが欠けているとValidationError"""
        data = {"long": "hello"}
        with pytest.raises(ValidationError) as exc_info:
            validate_dict_has_keys(data, ["long", "short"], "abstract")

        error_msg = str(exc_info.value)
        assert "short" in error_msg
        assert "missing required key" in error_msg

    @pytest.mark.unit
    def test_all_keys_missing_raises_error(self) -> None:
        """すべてのキーが欠けている場合もエラー"""
        data = {}
        with pytest.raises(ValidationError) as exc_info:
            validate_dict_has_keys(data, ["required"], "field")

        assert "required" in str(exc_info.value)

    @pytest.mark.unit
    def test_context_in_error_message(self) -> None:
        """エラーメッセージにコンテキストが含まれる"""
        with pytest.raises(ValidationError) as exc_info:
            validate_dict_has_keys({}, ["key"], "my_context")

        assert "my_context" in str(exc_info.value)


# =============================================================================
# validate_dict_key_type テスト
# =============================================================================


class TestValidateDictKeyType:
    """validate_dict_key_type 関数のテスト"""

    @pytest.mark.unit
    def test_valid_str_type_returns_value(self) -> None:
        """正しい型の値を返す"""
        data = {"name": "hello"}
        result = validate_dict_key_type(data, "name", str, "field")
        assert result == "hello"

    @pytest.mark.unit
    def test_valid_int_type_returns_value(self) -> None:
        """int型の値を返す"""
        data = {"count": 42}
        result = validate_dict_key_type(data, "count", int, "field")
        assert result == 42

    @pytest.mark.unit
    def test_valid_list_type_returns_value(self) -> None:
        """list型の値を返す"""
        data = {"items": [1, 2, 3]}
        result = validate_dict_key_type(data, "items", list, "field")
        assert result == [1, 2, 3]

    @pytest.mark.unit
    def test_missing_key_raises_validation_error(self) -> None:
        """キーが存在しないとValidationError"""
        data = {"other": "value"}
        with pytest.raises(ValidationError) as exc_info:
            validate_dict_key_type(data, "missing", str, "field")

        assert "missing required key" in str(exc_info.value)

    @pytest.mark.unit
    def test_wrong_type_raises_validation_error(self) -> None:
        """型が間違っているとValidationError"""
        data = {"name": 123}  # strを期待しているがint
        with pytest.raises(ValidationError) as exc_info:
            validate_dict_key_type(data, "name", str, "field")

        error_msg = str(exc_info.value)
        assert "expected str" in error_msg
        assert "got int" in error_msg

    @pytest.mark.unit
    def test_context_with_key_in_error(self) -> None:
        """エラーメッセージにコンテキストとキーが含まれる"""
        data = {"value": "string"}
        with pytest.raises(ValidationError) as exc_info:
            validate_dict_key_type(data, "value", int, "my_field")

        error_msg = str(exc_info.value)
        assert "my_field" in error_msg


# =============================================================================
# collect_list_element_errors テスト
# =============================================================================


class TestCollectListElementErrors:
    """collect_list_element_errors 関数のテスト"""

    @pytest.mark.unit
    def test_all_valid_no_errors(self) -> None:
        """すべての要素が正しい型ならエラーなし"""
        errors = []
        collect_list_element_errors(["a", "b", "c"], str, "paths", errors)
        assert errors == []

    @pytest.mark.unit
    def test_invalid_element_adds_error(self) -> None:
        """無効な要素があるとエラー追加"""
        errors = []
        collect_list_element_errors(["a", 123, "c"], str, "paths", errors)
        assert len(errors) == 1
        assert "paths[1]" in errors[0]
        assert "expected str" in errors[0]
        assert "got int" in errors[0]

    @pytest.mark.unit
    def test_multiple_invalid_elements(self) -> None:
        """複数の無効な要素があるとすべてエラー追加"""
        errors = []
        collect_list_element_errors([1, "wrong", 3, "also wrong"], int, "numbers", errors)
        assert len(errors) == 2
        assert "numbers[1]" in errors[0]
        assert "numbers[3]" in errors[1]

    @pytest.mark.unit
    def test_empty_list_no_errors(self) -> None:
        """空リストはエラーなし"""
        errors = []
        collect_list_element_errors([], str, "items", errors)
        assert errors == []

    @pytest.mark.unit
    def test_preserves_existing_errors(self) -> None:
        """既存のエラーを保持"""
        errors = ["existing error"]
        collect_list_element_errors([123], str, "field", errors)
        assert len(errors) == 2
        assert errors[0] == "existing error"

    @pytest.mark.unit
    def test_error_format(self) -> None:
        """エラーメッセージのフォーマット確認"""
        errors = []
        collect_list_element_errors(["valid", 999], str, "items", errors)

        # 期待: "items[1]: expected str, got int"
        assert "items[1]" in errors[0]
        assert "expected str" in errors[0]
        assert "got int" in errors[0]
