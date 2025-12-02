#!/usr/bin/env python3
"""
EpisodicRAG バリデーションユーティリティ
========================================

データ型検証の共通関数。domain層の関数をre-exportする薄いラッパー。

NOTE: 新規コードでは domain.validators を直接使用することを推奨:
    from domain.validators import is_valid_dict, is_valid_list

このモジュールは以下の理由で維持:
    - 既存のテストコードとの互換性
    - validate_source_files() のような複合バリデーション
    - get_dict_or_default(data, custom_default) のような拡張シグネチャ

Usage:
    from application.validators import validate_dict, validate_list, validate_source_files
"""

from typing import Any, Dict, List, Optional

from domain.validation import validate_type as _validate_type
from domain.validation_helpers import validate_list_not_empty as _validate_list_not_empty
from domain.validators import get_or_default as _get_or_default

# Re-export from domain.validators (SSoT)
from domain.validators import is_valid_dict, is_valid_list  # noqa: F401

__all__ = [
    "validate_dict",
    "validate_list",
    "validate_source_files",
    "is_valid_dict",
    "is_valid_list",
    "get_dict_or_default",
    "get_list_or_default",
]


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

    Note:
        domain.validation_helpers.validate_list_not_empty() に委譲。
    """
    return _validate_list_not_empty(files, context)


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
