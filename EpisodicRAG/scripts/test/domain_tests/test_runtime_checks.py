#!/usr/bin/env python3
"""
Runtime Checks Tests
====================

domain.validators.runtime_checks のテスト
"""

import pytest

from domain.exceptions import ValidationError
from domain.validators import ensure_not_none


class TestEnsureNotNone:
    """ensure_not_none のテスト"""

    # ==========================================================================
    # 正常ケース
    # ==========================================================================

    def test_returns_value_when_not_none(self) -> None:
        """Noneでない値はそのまま返す"""
        value = "hello"
        result = ensure_not_none(value, "test_context")
        assert result == "hello"

    def test_returns_empty_string(self) -> None:
        """空文字列はNoneではないので返す"""
        value = ""
        result = ensure_not_none(value, "empty_string")
        assert result == ""

    def test_returns_zero(self) -> None:
        """ゼロはNoneではないので返す"""
        value = 0
        result = ensure_not_none(value, "zero")
        assert result == 0

    def test_returns_false(self) -> None:
        """FalseはNoneではないので返す"""
        value = False
        result = ensure_not_none(value, "false")
        assert result is False

    def test_returns_empty_list(self) -> None:
        """空リストはNoneではないので返す"""
        value: list[str] = []
        result = ensure_not_none(value, "empty_list")
        assert result == []

    def test_returns_empty_dict(self) -> None:
        """空dictはNoneではないので返す"""
        value: dict[str, str] = {}
        result = ensure_not_none(value, "empty_dict")
        assert result == {}

    def test_returns_complex_object(self) -> None:
        """複雑なオブジェクトも返す"""
        value = {"key": [1, 2, 3], "nested": {"a": "b"}}
        result = ensure_not_none(value, "complex")
        assert result == value

    # ==========================================================================
    # エラーケース
    # ==========================================================================

    def test_raises_validation_error_when_none(self) -> None:
        """NoneのときはValidationErrorを投げる"""
        with pytest.raises(ValidationError) as exc_info:
            ensure_not_none(None, "test_context")
        assert "test_context" in str(exc_info.value)
        assert "expected non-None value" in str(exc_info.value)

    def test_error_message_includes_context(self) -> None:
        """エラーメッセージにコンテキストが含まれる"""
        with pytest.raises(ValidationError) as exc_info:
            ensure_not_none(None, "config.base_dir")
        assert "config.base_dir" in str(exc_info.value)

    def test_error_message_format(self) -> None:
        """エラーメッセージのフォーマットを確認"""
        with pytest.raises(ValidationError) as exc_info:
            ensure_not_none(None, "my_context")
        assert str(exc_info.value) == "my_context: expected non-None value"

    # ==========================================================================
    # 型推論テスト
    # ==========================================================================

    def test_type_narrowing_works(self) -> None:
        """型ナローイングが正しく機能する"""
        from typing import Optional

        value: str | None = "hello"
        # ensure_not_none の戻り値は str 型（Optional が外れる）
        result: str = ensure_not_none(value, "test")
        assert result == "hello"

    def test_preserves_type(self) -> None:
        """型を保持する"""
        from typing import Optional

        int_value: int | None = 42
        int_result: int = ensure_not_none(int_value, "int")
        assert int_result == 42

        list_value: list[str] | None = ["a", "b"]
        list_result: list[str] = ensure_not_none(list_value, "list")
        assert list_result == ["a", "b"]
