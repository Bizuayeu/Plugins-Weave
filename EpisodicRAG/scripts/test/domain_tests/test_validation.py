#!/usr/bin/env python3
"""
domain/validation.py のユニットテスト
=====================================

Domain層の型検証ユーティリティをテスト。
- validate_type: 例外を投げる型検証
- collect_type_error: エラーリストに追加する型検証
"""

import pytest
from domain.exceptions import ValidationError
from domain.validation import collect_type_error, validate_type


# =============================================================================
# validate_type テスト
# =============================================================================


class TestValidateType:
    """validate_type 関数のテスト"""

    @pytest.mark.unit
    def test_with_valid_dict(self):
        """dictを期待してdictを渡すとそのまま返す"""
        data = {"key": "value"}
        result = validate_type(data, dict, "test context", "dict")
        assert result == data
        assert result is data  # 同一オブジェクト

    @pytest.mark.unit
    def test_with_valid_list(self):
        """listを期待してlistを渡すとそのまま返す"""
        data = [1, 2, 3]
        result = validate_type(data, list, "test context", "list")
        assert result == data
        assert result is data

    @pytest.mark.unit
    def test_with_valid_str(self):
        """strを期待してstrを渡すとそのまま返す"""
        data = "hello"
        result = validate_type(data, str, "test context", "str")
        assert result == data

    @pytest.mark.unit
    def test_with_valid_int(self):
        """intを期待してintを渡すとそのまま返す"""
        data = 42
        result = validate_type(data, int, "test context", "int")
        assert result == data

    @pytest.mark.unit
    def test_with_empty_dict(self):
        """空のdictも有効"""
        data = {}
        result = validate_type(data, dict, "test context", "dict")
        assert result == {}

    @pytest.mark.unit
    def test_with_empty_list(self):
        """空のlistも有効"""
        data = []
        result = validate_type(data, list, "test context", "list")
        assert result == []

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "invalid_input,expected_type,type_name,actual_type_name",
        [
            (["item"], dict, "dict", "list"),
            ("string", dict, "dict", "str"),
            (None, dict, "dict", "NoneType"),
            (123, dict, "dict", "int"),
            ({"key": "value"}, list, "list", "dict"),
            (123, str, "str", "int"),
        ],
    )
    def test_with_invalid_type_raises_validation_error(
        self, invalid_input, expected_type, type_name, actual_type_name
    ):
        """型が一致しない場合はValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            validate_type(invalid_input, expected_type, "test context", type_name)

        error_message = str(exc_info.value)
        assert f"expected {type_name}" in error_message
        assert f"got {actual_type_name}" in error_message
        assert "test context" in error_message

    @pytest.mark.unit
    def test_error_message_contains_context(self):
        """エラーメッセージにコンテキストが含まれる"""
        with pytest.raises(ValidationError) as exc_info:
            validate_type("string", dict, "config.json", "dict")

        assert "config.json" in str(exc_info.value)

    @pytest.mark.unit
    def test_error_message_format(self):
        """エラーメッセージのフォーマットを確認"""
        with pytest.raises(ValidationError) as exc_info:
            validate_type([1, 2], dict, "my_context", "dict")

        # 期待: "my_context: expected dict, got list"
        assert str(exc_info.value) == "my_context: expected dict, got list"


# =============================================================================
# collect_type_error テスト
# =============================================================================


class TestCollectTypeError:
    """collect_type_error 関数のテスト"""

    @pytest.mark.unit
    def test_with_valid_type_no_error_added(self):
        """型が正しい場合はエラーリストに追加しない"""
        errors = []
        collect_type_error("value", str, "my_key", errors)
        assert errors == []

    @pytest.mark.unit
    def test_with_valid_int_no_error_added(self):
        """intが正しい場合はエラーリストに追加しない"""
        errors = []
        collect_type_error(42, int, "threshold", errors)
        assert errors == []

    @pytest.mark.unit
    def test_with_valid_dict_no_error_added(self):
        """dictが正しい場合はエラーリストに追加しない"""
        errors = []
        collect_type_error({"key": "value"}, dict, "config", errors)
        assert errors == []

    @pytest.mark.unit
    def test_with_invalid_type_adds_error(self):
        """型が間違っている場合はエラーリストに追加"""
        errors = []
        collect_type_error(123, str, "my_key", errors)
        assert len(errors) == 1
        assert "config['my_key']" in errors[0]
        assert "expected str" in errors[0]
        assert "got int" in errors[0]

    @pytest.mark.unit
    def test_with_none_adds_error(self):
        """Noneを渡すとエラー追加"""
        errors = []
        collect_type_error(None, str, "required_field", errors)
        assert len(errors) == 1
        assert "expected str" in errors[0]
        assert "got NoneType" in errors[0]

    @pytest.mark.unit
    def test_multiple_errors_accumulated(self):
        """複数のエラーが蓄積される"""
        errors = []
        collect_type_error(123, str, "field1", errors)
        collect_type_error("string", int, "field2", errors)
        collect_type_error([], dict, "field3", errors)

        assert len(errors) == 3
        assert "field1" in errors[0]
        assert "field2" in errors[1]
        assert "field3" in errors[2]

    @pytest.mark.unit
    def test_error_message_format(self):
        """エラーメッセージのフォーマットを確認"""
        errors = []
        collect_type_error([1, 2], str, "items", errors)

        # 期待: "config['items']: expected str, got list"
        assert errors[0] == "config['items']: expected str, got list"

    @pytest.mark.unit
    def test_does_not_raise_exception(self):
        """例外を投げずにエラーリストに追加のみ"""
        errors = []
        # 例外が発生しないことを確認
        collect_type_error("wrong", int, "key", errors)
        assert len(errors) == 1

    @pytest.mark.unit
    def test_preserves_existing_errors(self):
        """既存のエラーを保持しつつ追加"""
        errors = ["existing error"]
        collect_type_error(123, str, "new_key", errors)
        assert len(errors) == 2
        assert errors[0] == "existing error"
        assert "new_key" in errors[1]
