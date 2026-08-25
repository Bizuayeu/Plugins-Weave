#!/usr/bin/env python3
"""
File Scanner
============

ファイルシステムスキャンを担当するインフラストラクチャ層。
ディレクトリ内のファイル検出、パターンマッチングを提供。

Usage:
    from infrastructure.file_scanner import scan_files, get_files_by_pattern
"""

from collections.abc import Callable
from pathlib import Path


def scan_files(directory: Path, pattern: str = "*.txt", sort: bool = True) -> list[Path]:
    """
    指定ディレクトリ内のファイルをスキャン

    Args:
        directory: スキャンするディレクトリ
        pattern: ファイルパターン（glob形式）
        sort: ソートするかどうか（デフォルト: True）

    Returns:
        マッチしたファイルのPathリスト

    Example:
        >>> scan_files(Path("/data/loops"), "L*.txt")
        [Path("/data/loops/L00001.txt"), Path("/data/loops/L00002.txt")]
    """
    if not directory.exists():
        return []

    files = list(directory.glob(pattern))

    if sort:
        files = sorted(files)

    return files


def get_files_by_pattern(
    directory: Path, pattern: str, filter_func: Callable[[Path], bool] | None = None
) -> list[Path]:
    """
    パターンとフィルタ関数でファイルを取得

    Args:
        directory: スキャンするディレクトリ
        pattern: ファイルパターン（glob形式）
        filter_func: 追加のフィルタ関数（Trueを返すファイルのみ含める）

    Returns:
        マッチしたファイルのPathリスト（ソート済み）

    Example:
        >>> get_files_by_pattern(Path("/data"), "*.txt", lambda p: p.stat().st_size > 0)
        [Path("/data/file1.txt"), Path("/data/file2.txt")]
    """
    files = scan_files(directory, pattern, sort=True)

    if filter_func:
        files = [f for f in files if filter_func(f)]

    return files


def get_max_numbered_file(
    directory: Path, pattern: str, number_extractor: Callable[[str], int | None]
) -> int | None:
    """
    ディレクトリ内の最大番号を取得

    Args:
        directory: スキャンするディレクトリ
        pattern: ファイルパターン（glob形式）
        number_extractor: ファイル名から番号を抽出する関数

    Returns:
        最大番号（ファイルがなければNone）

    Example:
        >>> def extractor(name): return int(name[1:6]) if name.startswith("L") else None
        >>> get_max_numbered_file(Path("/data/loops"), "L*.txt", extractor)
        186
    """
    if not directory.exists():
        return None

    max_num = None

    for file in directory.glob(pattern):
        num = number_extractor(file.name)
        if num is not None and (max_num is None or num > max_num):
            max_num = num

    return max_num


def filter_files_after_number(
    files: list[Path], threshold: int, number_extractor: Callable[[str], int | None]
) -> list[Path]:
    """
    指定番号より大きいファイルのみをフィルタ

    Args:
        files: フィルタ対象のファイルリスト
        threshold: しきい値（この番号より大きいファイルを返す）
        number_extractor: ファイル名から番号を抽出する関数

    Returns:
        しきい値より大きい番号のファイルリスト

    Example:
        >>> files = [Path("L00001.txt"), Path("L00002.txt"), Path("L00003.txt")]
        >>> filter_files_after_number(files, 1, lambda n: int(n[1:6]))
        [Path("L00002.txt"), Path("L00003.txt")]
    """
    result = []

    for file in files:
        num = number_extractor(file.name)
        if num is not None and num > threshold:
            result.append(file)

    return result


def count_files(directory: Path, pattern: str = "*.txt") -> int:
    """
    パターンにマッチするファイル数をカウント

    Args:
        directory: スキャンするディレクトリ
        pattern: ファイルパターン（glob形式）

    Returns:
        マッチしたファイル数

    Example:
        >>> count_files(Path("/data/loops"), "L*.txt")
        186
    """
    if not directory.exists():
        return 0

    return len(list(directory.glob(pattern)))
