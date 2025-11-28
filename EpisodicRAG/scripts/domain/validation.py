#!/usr/bin/env python3
"""
Domain層 型検証ユーティリティ
=============================

外部依存を持たない純粋な型検証関数。
複数の層（Application, Config）から使用される共通ロジック。

Usage:
    from domain.validation import validate_type, collect_type_error
"""

from typing import Any, List, Type, TypeVar

from domain.exceptions import ValidationError

T = TypeVar("T")


def validate_type(data: Any, expected_type: Type[T], context: str, type_name: str) -> T:
    """
    汎用型検証（例外を投げる）

    Args:
        data: 検証対象のデータ
        expected_type: 期待する型
        context: エラーメッセージに含める文脈情報
        type_name: 表示用の型名

    Returns:
        検証済みのデータ

    Raises:
        ValidationError: dataが期待する型でない場合
    """
    if not isinstance(data, expected_type):
        raise ValidationError(f"{context}: expected {type_name}, got {type(data).__name__}")
    return data


def collect_type_error(value: Any, expected_type: Type[Any], key: str, errors: List[str]) -> None:
    """
    設定値の型検証を行い、エラーがあればリストに追加

    Args:
        value: 検証対象の値
        expected_type: 期待する型
        key: 設定キー名（エラーメッセージ用）
        errors: エラーメッセージを追加するリスト
    """
    if not isinstance(value, expected_type):
        errors.append(
            f"config['{key}']: expected {expected_type.__name__}, got {type(value).__name__}"
        )


__all__ = ["validate_type", "collect_type_error"]
