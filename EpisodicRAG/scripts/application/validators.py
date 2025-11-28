#!/usr/bin/env python3
"""
EpisodicRAG バリデーションユーティリティ
========================================

データ型検証の共通関数。
重複するisinstanceチェックを統一し、一貫したエラーメッセージを提供。

Usage:
    from application.validators import validate_dict, validate_list, validate_source_files

    data = validate_dict(raw_data, "config.json")
    files = validate_list(source_files, "source_files")
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from domain.exceptions import ValidationError
from domain.validation import validate_type as _validate_type

# =============================================================================
# 汎用ヘルパー関数（内部使用）
# =============================================================================

T = TypeVar('T')

# _validate_type は domain.validation から再エクスポート（後方互換性維持）


def _is_valid_type(data: Any, expected_type: Type[T]) -> bool:
    """
    汎用型チェックヘルパー（例外を投げない）

    Args:
        data: 検証対象のデータ
        expected_type: 期待する型

    Returns:
        dataが期待する型ならTrue
    """
    return isinstance(data, expected_type)


def _get_or_default(data: Any, expected_type: Type[T], default_factory: Callable[[], T]) -> T:
    """
    汎用デフォルト取得ヘルパー

    Args:
        data: 検証対象のデータ
        expected_type: 期待する型
        default_factory: デフォルト値を生成する関数

    Returns:
        dataが期待する型ならdata、そうでなければdefault_factory()の結果
    """
    if isinstance(data, expected_type):
        return data
    return default_factory()


# =============================================================================
# 公開API（後方互換性維持）
# =============================================================================


def validate_dict(data: Any, context: str) -> Dict[str, Any]:
    """
    データがdictであることを検証

    Args:
        data: 検証対象のデータ
        context: エラーメッセージに含める文脈情報

    Returns:
        検証済みのdict

    Raises:
        ValidationError: dataがdictでない場合
    """
    return _validate_type(data, dict, context, "dict")


def validate_list(data: Any, context: str) -> List[Any]:
    """
    データがlistであることを検証

    Args:
        data: 検証対象のデータ
        context: エラーメッセージに含める文脈情報

    Returns:
        検証済みのlist

    Raises:
        ValidationError: dataがlistでない場合
    """
    return _validate_type(data, list, context, "list")


def validate_source_files(files: Any, context: str = "source_files") -> List[str]:
    """
    source_filesの形式を検証

    Args:
        files: 検証対象のデータ
        context: エラーメッセージに含める文脈情報

    Returns:
        検証済みのファイルリスト

    Raises:
        ValidationError: filesがlistでない、または空の場合
    """
    if files is None:
        raise ValidationError(f"{context}: cannot be None")

    if not isinstance(files, list):
        raise ValidationError(f"{context}: expected list, got {type(files).__name__}")

    if not files:
        raise ValidationError(f"{context}: cannot be empty")

    return files


def is_valid_dict(data: Any) -> bool:
    """
    データがdictであるかをboolで返す（例外を投げない）

    Args:
        data: 検証対象のデータ

    Returns:
        dataがdictならTrue
    """
    return _is_valid_type(data, dict)


def is_valid_list(data: Any) -> bool:
    """
    データがlistであるかをboolで返す（例外を投げない）

    Args:
        data: 検証対象のデータ

    Returns:
        dataがlistならTrue
    """
    return _is_valid_type(data, list)


def get_dict_or_default(data: Any, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    dataがdictならそのまま返し、そうでなければデフォルト値を返す

    Args:
        data: 検証対象のデータ
        default: dataがdictでない場合の戻り値（デフォルト: 空のdict）

    Returns:
        dataがdictならdata、そうでなければdefault
    """
    return _get_or_default(data, dict, lambda: default if default is not None else {})


def get_list_or_default(data: Any, default: Optional[List[Any]] = None) -> List[Any]:
    """
    dataがlistならそのまま返し、そうでなければデフォルト値を返す

    Args:
        data: 検証対象のデータ
        default: dataがlistでない場合の戻り値（デフォルト: 空のlist）

    Returns:
        dataがlistならdata、そうでなければdefault
    """
    return _get_or_default(data, list, lambda: default if default is not None else [])
