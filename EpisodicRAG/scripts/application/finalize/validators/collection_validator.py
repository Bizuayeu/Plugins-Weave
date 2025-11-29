#!/usr/bin/env python3
"""
Collection Validator
====================

コレクション型（リスト、辞書等）の検証を担当するバリデータ
"""

from typing import Any, List, Optional

from domain.error_formatter import CompositeErrorFormatter, get_error_formatter
from domain.validators import is_valid_list


class CollectionValidator:
    """
    コレクション型の検証を担当

    Single Responsibility: コレクションの型チェックと空チェックのみを行う
    """

    def __init__(self, formatter: Optional[CompositeErrorFormatter] = None):
        """
        Args:
            formatter: エラーフォーマッタ（DIによるテスト容易化）
                      未指定時はグローバルシングルトンを使用
        """
        self._formatter = formatter

    @property
    def formatter(self) -> CompositeErrorFormatter:
        """遅延初期化でフォーマッタを取得"""
        if self._formatter is None:
            self._formatter = get_error_formatter()
        return self._formatter

    def validate_list(self, data: Any, context: str) -> List[str]:
        """
        データがリスト型かを検証

        Args:
            data: 検証対象のデータ
            context: エラーメッセージに含めるコンテキスト情報

        Returns:
            エラーメッセージのリスト（空の場合は検証成功）
        """
        if not is_valid_list(data):
            return [self.formatter.validation.invalid_type(context, "list", data)]
        return []

    def validate_non_empty(self, data: List[Any], context: str) -> List[str]:
        """
        リストが空でないかを検証

        Args:
            data: 検証対象のリスト
            context: エラーメッセージに含めるコンテキスト情報

        Returns:
            エラーメッセージのリスト（空の場合は検証成功）
        """
        if not data:
            return [self.formatter.validation.empty_collection(context)]
        return []

    def validate_list_and_non_empty(self, data: Any, context: str) -> List[str]:
        """
        データがリスト型かつ空でないかを検証（複合検証）

        Args:
            data: 検証対象のデータ
            context: エラーメッセージに含めるコンテキスト情報

        Returns:
            エラーメッセージのリスト（空の場合は検証成功）
        """
        errors = self.validate_list(data, context)
        if errors:
            return errors
        return self.validate_non_empty(data, context)
