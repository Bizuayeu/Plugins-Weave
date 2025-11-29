#!/usr/bin/env python3
"""
型検証ユーティリティ（Single Source of Truth）
===============================================

型検証の共通関数。重複するisinstanceチェックを統一し、
一貫したパターンを提供する。

Usage:
    from domain.validators.type_validators import (
        is_valid_type,
        get_or_default,
        is_valid_dict,
        is_valid_list,
    )

    # 型チェック（例外なし）
    if is_valid_dict(data):
        process(data)

    # デフォルト値付き取得
    files = get_or_default(data, list, list)
"""

from typing import Any, Callable, Dict, List, Type, TypeGuard, TypeVar

T = TypeVar("T")


# =============================================================================
# 基本型検証関数
# =============================================================================


def is_valid_type(data: Any, expected_type: Type[T]) -> bool:
    """
    汎用型チェックヘルパー（例外を投げない）

    Args:
        data: 検証対象のデータ
        expected_type: 期待する型

    Returns:
        dataが期待する型ならTrue

    Example:
        >>> is_valid_type({"key": "value"}, dict)
        True
        >>> is_valid_type([1, 2, 3], dict)
        False
    """
    return isinstance(data, expected_type)


def get_or_default(
    data: Any,
    expected_type: Type[T],
    default_factory: Callable[[], T],
) -> T:
    """
    汎用デフォルト取得ヘルパー

    Args:
        data: 検証対象のデータ
        expected_type: 期待する型
        default_factory: デフォルト値を生成する関数

    Returns:
        dataが期待する型ならdata、そうでなければdefault_factory()の結果

    Example:
        >>> get_or_default({"key": "value"}, dict, dict)
        {"key": "value"}
        >>> get_or_default(None, dict, dict)
        {}
    """
    if isinstance(data, expected_type):
        return data
    return default_factory()


# =============================================================================
# TypeGuard関数（型絞り込み用）
# =============================================================================


def is_valid_dict(data: Any) -> TypeGuard[Dict[str, Any]]:
    """
    データがdictであるかをboolで返す（TypeGuard付き）

    型絞り込みにより、Trueの場合はDict[str, Any]として扱える。

    Args:
        data: 検証対象のデータ

    Returns:
        dataがdictならTrue

    Example:
        >>> data: Any = {"key": "value"}
        >>> if is_valid_dict(data):
        ...     # data は Dict[str, Any] として型推論される
        ...     print(data.keys())
    """
    return isinstance(data, dict)


def is_valid_list(data: Any) -> TypeGuard[List[Any]]:
    """
    データがlistであるかをboolで返す（TypeGuard付き）

    型絞り込みにより、Trueの場合はList[Any]として扱える。

    Args:
        data: 検証対象のデータ

    Returns:
        dataがlistならTrue

    Example:
        >>> data: Any = [1, 2, 3]
        >>> if is_valid_list(data):
        ...     # data は List[Any] として型推論される
        ...     print(len(data))
    """
    return isinstance(data, list)


def is_valid_str(data: Any) -> TypeGuard[str]:
    """
    データがstrであるかをboolで返す（TypeGuard付き）

    Args:
        data: 検証対象のデータ

    Returns:
        dataがstrならTrue
    """
    return isinstance(data, str)


def is_valid_int(data: Any) -> TypeGuard[int]:
    """
    データがintであるかをboolで返す（TypeGuard付き）

    Note:
        boolはintのサブクラスなので、bool値もTrueを返す。
        純粋なintのみを判定したい場合は、
        `is_valid_int(data) and not isinstance(data, bool)` を使用。

    Args:
        data: 検証対象のデータ

    Returns:
        dataがintならTrue
    """
    return isinstance(data, int)


# =============================================================================
# 便利なデフォルト取得関数
# =============================================================================


def get_dict_or_empty(data: Any) -> Dict[str, Any]:
    """
    dataがdictならそのまま返し、そうでなければ空のdictを返す

    Args:
        data: 検証対象のデータ

    Returns:
        dataがdictならdata、そうでなければ{}
    """
    return get_or_default(data, dict, dict)


def get_list_or_empty(data: Any) -> List[Any]:
    """
    dataがlistならそのまま返し、そうでなければ空のlistを返す

    Args:
        data: 検証対象のデータ

    Returns:
        dataがlistならdata、そうでなければ[]
    """
    return get_or_default(data, list, list)


def get_str_or_empty(data: Any) -> str:
    """
    dataがstrならそのまま返し、そうでなければ空の文字列を返す

    Args:
        data: 検証対象のデータ

    Returns:
        dataがstrならdata、そうでなければ""
    """
    return get_or_default(data, str, str)
