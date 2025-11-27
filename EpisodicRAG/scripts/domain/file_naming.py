#!/usr/bin/env python3
"""
File Naming Utilities
=====================

ファイル名のパース・フォーマットに関するドメインロジック

Usage:
    from domain.file_naming import extract_file_number, format_digest_number
"""
import re
from typing import Optional, Tuple

from domain.constants import LEVEL_CONFIG, LEVEL_NAMES


def extract_file_number(filename: str) -> Optional[Tuple[str, int]]:
    """
    ファイル名からプレフィックスと番号を抽出

    Args:
        filename: ファイル名（例: "Loop0186_xxx.txt", "MD01_xxx.txt"）

    Returns:
        (prefix, number) のタプル、またはNone

    Examples:
        >>> extract_file_number("Loop0186_test.txt")
        ('Loop', 186)
        >>> extract_file_number("W0001_weekly.txt")
        ('W', 1)
        >>> extract_file_number("MD03_decadal.txt")
        ('MD', 3)
    """
    # 型チェック
    if not isinstance(filename, str):
        return None

    # MDプレフィックス（2文字）を先にチェック（M単独より優先）
    match = re.search(r'(Loop|MD)(\d+)', filename)
    if match:
        return (match.group(1), int(match.group(2)))

    # 1文字プレフィックス
    match = re.search(r'([WMQATDC])(\d+)', filename)
    if match:
        return (match.group(1), int(match.group(2)))

    return None


def extract_number_only(filename: str) -> Optional[int]:
    """
    ファイル名から番号のみを抽出（後方互換性用）

    Args:
        filename: ファイル名

    Returns:
        番号、またはNone

    Examples:
        >>> extract_number_only("Loop0186_test.txt")
        186
    """
    result = extract_file_number(filename)
    return result[1] if result else None


def format_digest_number(level: str, number: int) -> str:
    """
    レベルと番号から統一されたフォーマットの文字列を生成

    Args:
        level: 階層名（"loop", "weekly", "monthly", ...）
        number: 番号

    Returns:
        ゼロ埋めされた文字列（例: "Loop0186", "W0001", "MD01"）

    Raises:
        ValueError: 不正なレベル名の場合

    Examples:
        >>> format_digest_number("loop", 186)
        'Loop0186'
        >>> format_digest_number("weekly", 1)
        'W0001'
        >>> format_digest_number("multi_decadal", 3)
        'MD03'
    """
    if level == "loop":
        return f"Loop{number:04d}"

    if level not in LEVEL_CONFIG:
        raise ValueError(f"Invalid level: {level}. Valid levels: {LEVEL_NAMES + ['loop']}")

    config = LEVEL_CONFIG[level]
    return f"{config['prefix']}{number:0{config['digits']}d}"


__all__ = [
    "extract_file_number",
    "extract_number_only",
    "format_digest_number",
]
