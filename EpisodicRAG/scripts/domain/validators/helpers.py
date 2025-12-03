#!/usr/bin/env python3
"""
バリデーションヘルパー関数
==========================

例外を投げる型検証と、エラー収集関数を提供。

Usage:
    from domain.validators.helpers import (
        validate_type,
        collect_type_error,
        validate_list_not_empty,
        validate_dict_has_keys,
        validate_dict_key_type,
        collect_list_element_errors,
    )
"""

from typing import Any, Dict, List, Sequence, Type, TypeVar

from domain.error_formatter import get_error_formatter
from domain.exceptions import ValidationError

T = TypeVar("T")


# =============================================================================
# 例外を投げる検証関数
# =============================================================================


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
        formatter = get_error_formatter()
        raise ValidationError(formatter.validation.invalid_type(context, type_name, data))
    return data


def validate_list_not_empty(
    value: Any,
    context: str,
) -> List[Any]:
    """
    リストがNoneでなく空でないことを検証

    Args:
        value: 検証対象の値
        context: エラーメッセージに含める文脈情報

    Returns:
        検証済みのリスト

    Raises:
        ValidationError: valueがNone、list以外、または空の場合

    Example:
        >>> validate_list_not_empty([1, 2, 3], "source_files")
        [1, 2, 3]
        >>> validate_list_not_empty(None, "source_files")
        ValidationError: source_files: cannot be None
    """
    formatter = get_error_formatter()

    if value is None:
        raise ValidationError(
            formatter.validation.validation_error(context, "cannot be None", None)
        )

    if not isinstance(value, list):
        raise ValidationError(formatter.validation.invalid_type(context, "list", value))

    if not value:
        raise ValidationError(formatter.validation.empty_collection(context))

    return value


def validate_dict_has_keys(
    data: Dict[str, Any],
    required_keys: Sequence[str],
    context: str,
) -> None:
    """
    辞書に必須キーが存在することを検証

    Args:
        data: 検証対象の辞書
        required_keys: 必須キーのシーケンス
        context: エラーメッセージに含める文脈情報

    Raises:
        ValidationError: 必須キーが存在しない場合

    Example:
        >>> validate_dict_has_keys({"long": "a", "short": "b"}, ["long", "short"], "abstract")
        None  # 成功
        >>> validate_dict_has_keys({"long": "a"}, ["long", "short"], "abstract")
        ValidationError: abstract: missing required key 'short'
    """
    formatter = get_error_formatter()

    for key in required_keys:
        if key not in data:
            raise ValidationError(
                formatter.validation.validation_error(
                    context, f"missing required key '{key}'", None
                )
            )


def validate_dict_key_type(
    data: Dict[str, Any],
    key: str,
    expected_type: Type[T],
    context: str,
) -> T:
    """
    辞書の特定キーの値の型を検証

    Args:
        data: 検証対象の辞書
        key: チェックするキー
        expected_type: 期待する型
        context: エラーメッセージに含める文脈情報

    Returns:
        検証済みの値

    Raises:
        ValidationError: キーが存在しない、または値の型が期待と異なる場合

    Example:
        >>> data = {"long": "hello", "short": "hi"}
        >>> validate_dict_key_type(data, "long", str, "abstract")
        "hello"
    """
    formatter = get_error_formatter()

    if key not in data:
        raise ValidationError(
            formatter.validation.validation_error(context, f"missing required key '{key}'", None)
        )

    value = data[key]
    if not isinstance(value, expected_type):
        raise ValidationError(
            formatter.validation.invalid_type(f"{context}.{key}", expected_type.__name__, value)
        )

    return value


# =============================================================================
# エラー収集関数（例外を投げない）
# =============================================================================


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


def collect_list_element_errors(
    lst: List[Any],
    expected_type: Type[Any],
    context: str,
    errors: List[str],
) -> None:
    """
    リスト要素の型を検証し、エラーをリストに蓄積

    Args:
        lst: 検証対象のリスト
        expected_type: 期待する要素の型
        context: エラーメッセージに含める文脈情報
        errors: エラーメッセージを蓄積するリスト

    Example:
        >>> errors = []
        >>> collect_list_element_errors(["a", "b", 123], str, "paths", errors)
        >>> errors
        ["paths[2]: expected str, got int"]
    """
    for i, item in enumerate(lst):
        if not isinstance(item, expected_type):
            errors.append(
                f"{context}[{i}]: expected {expected_type.__name__}, got {type(item).__name__}"
            )


__all__ = [
    # Throwing validators
    "validate_type",
    "validate_list_not_empty",
    "validate_dict_has_keys",
    "validate_dict_key_type",
    # Error collectors
    "collect_type_error",
    "collect_list_element_errors",
]
