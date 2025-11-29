#!/usr/bin/env python3
"""
CollectionValidator のユニットテスト
====================================

コレクション型（リスト）の検証機能を個別にテスト。
ShadowValidatorの統合テストで間接的にカバーされているが、
専用テストでバリデータの契約を明示的にドキュメント化。
"""

from unittest.mock import MagicMock

import pytest

from application.finalize.validators.collection_validator import CollectionValidator
from domain.error_formatter import CompositeErrorFormatter

# 全テストにunitマーカーを適用
pytestmark = pytest.mark.unit


# =============================================================================
# 初期化テスト
# =============================================================================


class TestCollectionValidatorInit:
    """CollectionValidator 初期化のテスト"""

    def test_init_with_default_formatter(self):
        """デフォルトフォーマッタで初期化"""
        validator = CollectionValidator()
        # フォーマッタは遅延初期化されるので、この時点ではNone
        assert validator._formatter is None

    def test_init_with_custom_formatter(self):
        """カスタムフォーマッタで初期化"""
        mock_formatter = MagicMock(spec=CompositeErrorFormatter)
        validator = CollectionValidator(formatter=mock_formatter)
        assert validator._formatter is mock_formatter

    def test_formatter_lazy_initialization(self):
        """formatterプロパティで遅延初期化される"""
        validator = CollectionValidator()
        assert validator._formatter is None

        # formatterプロパティにアクセスすると初期化される
        formatter = validator.formatter
        assert formatter is not None
        assert isinstance(formatter, CompositeErrorFormatter)

        # 2回目のアクセスで同じインスタンスが返される
        assert validator.formatter is formatter


# =============================================================================
# validate_list メソッドのテスト
# =============================================================================


class TestValidateList:
    """validate_list メソッドのテスト"""

    @pytest.fixture
    def validator(self):
        """テスト用CollectionValidator"""
        return CollectionValidator()

    # -------------------------------------------------------------------------
    # 正常系
    # -------------------------------------------------------------------------

    def test_valid_list_returns_empty_errors(self, validator):
        """有効なリストはエラーなし"""
        errors = validator.validate_list([1, 2, 3], "test_context")
        assert errors == []

    def test_empty_list_is_valid_type(self, validator):
        """空のリストも型としては有効"""
        errors = validator.validate_list([], "test_context")
        assert errors == []

    def test_nested_list_is_valid_type(self, validator):
        """ネストされたリストも有効"""
        errors = validator.validate_list([[1, 2], [3, 4]], "test_context")
        assert errors == []

    def test_list_with_mixed_types(self, validator):
        """異なる型を含むリストも有効"""
        errors = validator.validate_list([1, "string", None, {"key": "value"}], "test_context")
        assert errors == []

    # -------------------------------------------------------------------------
    # 異常系（parametrized）
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "invalid_input,type_name",
        [
            ("string", "str"),
            (123, "int"),
            (12.34, "float"),
            ({"key": "value"}, "dict"),
            ((1, 2, 3), "tuple"),
            (None, "NoneType"),
            (True, "bool"),
        ],
    )
    def test_non_list_types_return_error(self, validator, invalid_input, type_name):
        """リスト以外の型はエラーを返す"""
        errors = validator.validate_list(invalid_input, "test_context")
        assert len(errors) == 1
        assert "expected list" in errors[0].lower()

    # -------------------------------------------------------------------------
    # エラーメッセージ検証
    # -------------------------------------------------------------------------

    def test_error_message_contains_context(self, validator):
        """エラーメッセージにコンテキストが含まれる"""
        context = "source_files"
        errors = validator.validate_list("not a list", context)
        assert len(errors) == 1
        assert context in errors[0]

    def test_error_message_contains_actual_type(self, validator):
        """エラーメッセージに実際の型が含まれる"""
        errors = validator.validate_list({"dict": "value"}, "test_context")
        assert len(errors) == 1
        assert "dict" in errors[0].lower()


# =============================================================================
# validate_non_empty メソッドのテスト
# =============================================================================


class TestValidateNonEmpty:
    """validate_non_empty メソッドのテスト"""

    @pytest.fixture
    def validator(self):
        """テスト用CollectionValidator"""
        return CollectionValidator()

    # -------------------------------------------------------------------------
    # 正常系
    # -------------------------------------------------------------------------

    def test_non_empty_list_returns_empty_errors(self, validator):
        """空でないリストはエラーなし"""
        errors = validator.validate_non_empty([1, 2, 3], "test_context")
        assert errors == []

    def test_single_element_list_returns_empty_errors(self, validator):
        """1要素のリストもエラーなし"""
        errors = validator.validate_non_empty(["single"], "test_context")
        assert errors == []

    def test_list_with_none_elements_is_non_empty(self, validator):
        """Noneを含むリストは空ではない"""
        errors = validator.validate_non_empty([None], "test_context")
        assert errors == []

    def test_list_with_empty_string_is_non_empty(self, validator):
        """空文字列を含むリストは空ではない"""
        errors = validator.validate_non_empty([""], "test_context")
        assert errors == []

    # -------------------------------------------------------------------------
    # 異常系
    # -------------------------------------------------------------------------

    def test_empty_list_returns_error(self, validator):
        """空のリストはエラーを返す"""
        errors = validator.validate_non_empty([], "test_context")
        assert len(errors) == 1
        assert "cannot be empty" in errors[0].lower() or "empty" in errors[0].lower()

    def test_error_message_contains_context(self, validator):
        """エラーメッセージにコンテキストが含まれる"""
        context = "source_files"
        errors = validator.validate_non_empty([], context)
        assert len(errors) == 1
        assert context in errors[0]


# =============================================================================
# validate_list_and_non_empty 複合検証テスト
# =============================================================================


class TestValidateListAndNonEmpty:
    """validate_list_and_non_empty 複合検証テスト"""

    @pytest.fixture
    def validator(self):
        """テスト用CollectionValidator"""
        return CollectionValidator()

    # -------------------------------------------------------------------------
    # 正常系
    # -------------------------------------------------------------------------

    def test_valid_non_empty_list_returns_empty_errors(self, validator):
        """有効な非空リストはエラーなし"""
        errors = validator.validate_list_and_non_empty([1, 2, 3], "test_context")
        assert errors == []

    def test_single_element_list_passes(self, validator):
        """1要素のリストもエラーなし"""
        errors = validator.validate_list_and_non_empty(["item"], "test_context")
        assert errors == []

    # -------------------------------------------------------------------------
    # 異常系：型エラーが先に検出される
    # -------------------------------------------------------------------------

    def test_non_list_returns_type_error_only(self, validator):
        """リスト以外の型は型エラーのみ返す（空チェックは行わない）"""
        errors = validator.validate_list_and_non_empty("not a list", "test_context")
        assert len(errors) == 1
        assert "expected list" in errors[0].lower()

    def test_dict_returns_type_error_only(self, validator):
        """dictは型エラーのみ返す"""
        errors = validator.validate_list_and_non_empty({"key": "value"}, "test_context")
        assert len(errors) == 1
        assert "expected list" in errors[0].lower()

    # -------------------------------------------------------------------------
    # 異常系：型OK、空チェックでエラー
    # -------------------------------------------------------------------------

    def test_empty_list_returns_empty_error(self, validator):
        """空のリストは空エラーを返す"""
        errors = validator.validate_list_and_non_empty([], "test_context")
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    # -------------------------------------------------------------------------
    # 型エラーが優先される
    # -------------------------------------------------------------------------

    def test_type_error_takes_precedence_over_empty(self, validator):
        """型エラーは空チェックより優先（空文字列の場合）"""
        # 空文字列はリストではないので、型エラーが先に検出される
        errors = validator.validate_list_and_non_empty("", "test_context")
        assert len(errors) == 1
        assert "expected list" in errors[0].lower()


# =============================================================================
# エッジケーステスト
# =============================================================================


class TestCollectionValidatorEdgeCases:
    """CollectionValidator のエッジケーステスト"""

    @pytest.fixture
    def validator(self):
        """テスト用CollectionValidator"""
        return CollectionValidator()

    def test_unicode_context_in_error_message(self, validator):
        """日本語コンテキストがエラーメッセージに含まれる"""
        context = "ソースファイル"
        errors = validator.validate_list("not a list", context)
        assert len(errors) == 1
        assert context in errors[0]

    def test_very_long_context_string(self, validator):
        """非常に長いコンテキスト文字列でも動作する"""
        context = "a" * 1000
        errors = validator.validate_list("not a list", context)
        assert len(errors) == 1
        # エラーメッセージは生成されるが、長さの制限はない
        assert errors[0] is not None

    def test_special_characters_in_context(self, validator):
        """特殊文字を含むコンテキストでも動作する"""
        context = "source_files[0]['name']"
        errors = validator.validate_list("not a list", context)
        assert len(errors) == 1
        assert context in errors[0]

    def test_newline_in_context(self, validator):
        """改行を含むコンテキストでも動作する"""
        context = "line1\nline2"
        errors = validator.validate_list("not a list", context)
        assert len(errors) == 1
        # エラーメッセージは生成される
        assert errors[0] is not None

    def test_large_list_validation(self, validator):
        """大きなリストでも正常に動作する"""
        large_list = list(range(10000))
        errors = validator.validate_list(large_list, "test_context")
        assert errors == []

        errors = validator.validate_non_empty(large_list, "test_context")
        assert errors == []
