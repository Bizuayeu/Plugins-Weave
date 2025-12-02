#!/usr/bin/env python3
"""
EpisodicRAG テキスト抽出ユーティリティ
======================================

LongShortText型からlong/short版の値を抽出するユーティリティ関数。

Usage:
    from domain.text_utils import extract_long_value, extract_short_value
"""

from typing import Any

from domain.types import LongShortText


def extract_long_value(text: Any, default: str = "") -> str:
    """
    LongShortTextまたは文字列からlong版の値を抽出（overall_digest用）

    Args:
        text: LongShortText型 または 文字列
        default: 値が取得できない場合のデフォルト値

    Returns:
        long版の文字列（文字列の場合はそのまま返す）

    Example:
        >>> extract_long_value({"long": "2400字...", "short": "1200字..."})
        '2400字...'
        >>> extract_long_value("plain text")
        'plain text'

    Note:
        OverallDigestData（Shadow）は単純文字列を使用するため、
        両形式をサポート。
    """
    if isinstance(text, dict):
        return text.get("long", default)
    if isinstance(text, str):
        return text if text else default
    return default


def extract_short_value(text: LongShortText, default: str = "") -> str:
    """
    LongShortTextからshort版の値を抽出（individual_digests用）

    Args:
        text: LongShortText型のデータ
        default: 値が取得できない場合のデフォルト値

    Returns:
        short版の文字列

    Example:
        >>> extract_short_value({"long": "2400字...", "short": "1200字..."})
        '1200字...'
    """
    if isinstance(text, dict):
        return text.get("short", default)
    return default


def extract_value(text: Any, key: str, default: str = "") -> str:
    """
    任意のキーで値を抽出する汎用関数

    Args:
        text: 辞書型のデータ
        key: 抽出するキー（"long" or "short"）
        default: 値が取得できない場合のデフォルト値

    Returns:
        指定キーの文字列値

    Example:
        >>> extract_value({"long": "詳細", "short": "簡潔"}, "long")
        '詳細'
    """
    if isinstance(text, dict):
        return text.get(key, default)
    return default
