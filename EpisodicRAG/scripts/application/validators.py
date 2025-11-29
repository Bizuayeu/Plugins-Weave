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

from typing import Any, Dict, List, Optional

from domain.error_formatter import get_error_formatter
from domain.exceptions import ValidationError
from domain.validation import validate_type as _validate_type
from domain.validators import (
    get_or_default as _get_or_default,
    is_valid_type as _is_valid_type,
)


# =============================================================================
# 公開API（後方互換性維持）
# =============================================================================
#
# NOTE: これらの関数はdomain層の検証関数への薄いラッパーです。
# domain.validation および domain.validators に直接アクセスすることも可能ですが、
# 既存コードとの後方互換性を維持するためにこのモジュールを提供しています。
#
# 新規コードでは、用途に応じて以下を直接使用することを推奨:
#   - domain.validation.validate_type() - 型検証（例外を投げる）
#   - domain.validators.is_valid_type() - 型チェック（boolを返す）
#   - domain.validators.get_or_default() - デフォルト値付き取得
#


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
    formatter = get_error_formatter()
    if files is None:
        raise ValidationError(formatter.validation.validation_error(context, "cannot be None", None))

    if not isinstance(files, list):
        raise ValidationError(formatter.validation.invalid_type(context, "list", files))

    if not files:
        raise ValidationError(formatter.validation.empty_collection(context))

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
