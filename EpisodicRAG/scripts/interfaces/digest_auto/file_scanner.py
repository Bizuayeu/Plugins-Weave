#!/usr/bin/env python3
"""
Digest Auto File Scanner
========================

ファイルスキャンとギャップ検出のユーティリティ。

Functions:
    extract_file_number: ファイル名から番号を抽出
    find_gaps: 連番のギャップを検出
"""

import re
from typing import List, Optional

__all__ = [
    "extract_file_number",
    "find_gaps",
]


def extract_file_number(filename: str) -> Optional[int]:
    """ファイル名から番号を抽出

    L00001, W0001, M001 などのパターンにマッチし、番号部分を返す。

    Args:
        filename: ファイル名（拡張子なしでも可）

    Returns:
        抽出された番号、またはマッチしない場合はNone

    Examples:
        >>> extract_file_number("L00001_summary.txt")
        1
        >>> extract_file_number("W0042")
        42
        >>> extract_file_number("readme.txt")
        None
    """
    match = re.search(r"[A-Z]+(\d+)", filename)
    if match:
        return int(match.group(1))
    return None


def find_gaps(numbers: List[int]) -> List[int]:
    """連番のギャップを検出

    与えられた数値リストの最小値から最大値の間で、
    欠けている数値を検出して返す。

    Args:
        numbers: 数値のリスト

    Returns:
        欠けている数値のリスト

    Examples:
        >>> find_gaps([1, 2, 5])
        [3, 4]
        >>> find_gaps([1, 2, 3])
        []
        >>> find_gaps([10])
        []
    """
    if len(numbers) < 2:
        return []

    sorted_nums = sorted(numbers)
    gaps = []
    for i in range(len(sorted_nums) - 1):
        for n in range(sorted_nums[i] + 1, sorted_nums[i + 1]):
            gaps.append(n)
    return gaps
