#!/usr/bin/env python3
"""
バリデーション関連エラーフォーマッタ
====================================

型チェック、値検証、コレクション検証に関するエラーメッセージを生成。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
このクラスは「バリデーションエラーのフォーマット」という単一責務のみを持つ。
"""

from typing import Any, Optional

from domain.error_formatter.base import BaseErrorFormatter


class ValidationErrorFormatter(BaseErrorFormatter):
    """
    バリデーション関連エラーのフォーマッタ

    型チェック、値検証、コレクション検証に関するエラーメッセージを
    一貫したフォーマットで生成する。

    Example:
        formatter = ValidationErrorFormatter(project_root)
        msg = formatter.invalid_type("user_id", "int", "hello")
        # -> "user_id: expected int, got str"
    """

    def invalid_type(self, context: str, expected: str, actual: Any) -> str:
        """
        型不正エラーメッセージ

        Args:
            context: エラーが発生したコンテキスト（フィールド名など）
            expected: 期待される型名
            actual: 実際の値

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"{context}: expected {expected}, got {type(actual).__name__}"

    def validation_error(self, field: str, reason: str, value: Optional[Any] = None) -> str:
        """
        バリデーションエラーメッセージ

        Args:
            field: バリデーションに失敗したフィールド名
            reason: 失敗の理由
            value: 実際の値（省略可能）

        Returns:
            フォーマットされたエラーメッセージ
        """
        if value is not None:
            return f"Validation failed for '{field}': {reason} (got: {value})"
        return f"Validation failed for '{field}': {reason}"

    def empty_collection(self, context: str) -> str:
        """
        空コレクションエラーメッセージ

        Args:
            context: エラーが発生したコンテキスト

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"{context} cannot be empty"
