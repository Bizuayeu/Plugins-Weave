#!/usr/bin/env python3
"""
Config層専用のバリデーション
============================

Config層をDomain層から独立させるためのバリデーションユーティリティ。

Usage:
    from config.validation import collect_type_error
"""

from typing import Any, List, Type


def collect_type_error(
    value: Any,
    expected_type: Type[Any],
    key: str,
    errors: List[str],
) -> None:
    """
    型を検証し、不正な場合はエラーメッセージをリストに追加

    Args:
        value: 検証対象の値
        expected_type: 期待される型
        key: 設定キー名（エラーメッセージ用）
        errors: エラーメッセージを追加するリスト

    Example:
        >>> errors: List[str] = []
        >>> collect_type_error("not_an_int", int, "threshold", errors)
        >>> print(errors)
        ["config['threshold']: expected int, got str"]
    """
    if not isinstance(value, expected_type):
        errors.append(
            f"config['{key}']: expected {expected_type.__name__}, got {type(value).__name__}"
        )
