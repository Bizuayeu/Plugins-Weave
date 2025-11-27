#!/usr/bin/env python3
"""
File Naming Utilities
=====================

ファイル名のパース・フォーマットに関するドメインロジック

Usage:
    from domain.file_naming import extract_file_number, format_digest_number
    from domain.file_naming import find_max_number, filter_files_after
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple, Union

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


def find_max_number(files: List[Union[Path, str]], prefix: str) -> Optional[int]:
    """
    ファイルリストから指定プレフィックスの最大番号を取得

    Args:
        files: ファイルパス（PathまたはStr）のリスト
        prefix: 検索するプレフィックス（例: "W", "Loop", "MD"）

    Returns:
        最大番号、またはマッチするファイルがない場合はNone

    Examples:
        >>> find_max_number(["W0001_a.txt", "W0003_b.txt"], "W")
        3
        >>> find_max_number(["M001_a.txt"], "W")
        None
    """
    if not files:
        return None

    max_num: Optional[int] = None

    for file in files:
        # PathオブジェクトまたはStringからファイル名を取得
        if isinstance(file, Path):
            filename = file.name
        elif isinstance(file, str):
            filename = Path(file).name if "/" in file or "\\" in file else file
        else:
            continue

        result = extract_file_number(filename)
        if result and result[0] == prefix:
            num = result[1]
            if max_num is None or num > max_num:
                max_num = num

    return max_num


def filter_files_after(files: List[Path], threshold: int) -> List[Path]:
    """
    閾値より大きい番号のファイルをフィルタ

    Args:
        files: ファイルパス（Path）のリスト
        threshold: この番号より大きいファイルを返す

    Returns:
        閾値より大きい番号のファイルリスト

    Examples:
        >>> filter_files_after([Path("Loop0001.txt"), Path("Loop0005.txt")], 2)
        [Path("Loop0005.txt")]
    """
    if not files:
        return []

    result = []
    for file in files:
        file_num = extract_number_only(file.name)
        if file_num is not None and file_num > threshold:
            result.append(file)

    return result


def extract_numbers_formatted(files: List[Union[str, None]]) -> List[str]:
    """
    ファイル名リストからフォーマット済み番号リストを抽出

    各ファイル名からプレフィックスと番号を抽出し、
    format_digest_number()を使用して統一フォーマットに変換。
    結果はソートされて返される。

    Args:
        files: ファイル名のリスト

    Returns:
        フォーマット済み番号のソート済みリスト（例: ["Loop0001", "Loop0002"]）

    Examples:
        >>> extract_numbers_formatted(["Loop0003_c.txt", "Loop0001_a.txt"])
        ["Loop0001", "Loop0003"]
    """
    if not files:
        return []

    # プレフィックス→レベル の逆引きマップ
    prefix_to_level = {cfg["prefix"]: lvl for lvl, cfg in LEVEL_CONFIG.items()}

    numbers = []
    for file in files:
        # 型チェック
        if not isinstance(file, str):
            continue

        result = extract_file_number(file)
        if result:
            prefix, num = result
            # format_digest_number を使用して統一されたフォーマットを生成
            if prefix == "Loop":
                numbers.append(format_digest_number("loop", num))
            else:
                source_level = prefix_to_level.get(prefix)
                if source_level:
                    numbers.append(format_digest_number(source_level, num))
                else:
                    # 未知のプレフィックス: 元の形式を維持（フォールバック）
                    numbers.append(f"{prefix}{num:04d}")

    return sorted(numbers)


__all__ = [
    "extract_file_number",
    "extract_number_only",
    "format_digest_number",
    "find_max_number",
    "filter_files_after",
    "extract_numbers_formatted",
]
