#!/usr/bin/env python3
"""
File Scanner
============

ファイルシステムスキャンを担当するインフラストラクチャ層。
ディレクトリ内のファイル検出、パターンマッチングを提供。

Usage:
    from infrastructure.file_scanner import scan_files, get_files_by_pattern
"""
from pathlib import Path
from typing import List, Optional, Callable


def scan_files(
    directory: Path,
    pattern: str = "*.txt",
    sort: bool = True
) -> List[Path]:
    """
    指定ディレクトリ内のファイルをスキャン

    Args:
        directory: スキャンするディレクトリ
        pattern: ファイルパターン（glob形式）
        sort: ソートするかどうか（デフォルト: True）

    Returns:
        マッチしたファイルのPathリスト
    """
    if not directory.exists():
        return []

    files = list(directory.glob(pattern))

    if sort:
        files = sorted(files)

    return files


def get_files_by_pattern(
    directory: Path,
    pattern: str,
    filter_func: Optional[Callable[[Path], bool]] = None
) -> List[Path]:
    """
    パターンとフィルタ関数でファイルを取得

    Args:
        directory: スキャンするディレクトリ
        pattern: ファイルパターン（glob形式）
        filter_func: 追加のフィルタ関数（Trueを返すファイルのみ含める）

    Returns:
        マッチしたファイルのPathリスト（ソート済み）
    """
    files = scan_files(directory, pattern, sort=True)

    if filter_func:
        files = [f for f in files if filter_func(f)]

    return files


def get_max_numbered_file(
    directory: Path,
    pattern: str,
    number_extractor: Callable[[str], Optional[int]]
) -> Optional[int]:
    """
    ディレクトリ内の最大番号を取得

    Args:
        directory: スキャンするディレクトリ
        pattern: ファイルパターン（glob形式）
        number_extractor: ファイル名から番号を抽出する関数

    Returns:
        最大番号（ファイルがなければNone）
    """
    if not directory.exists():
        return None

    max_num = None

    for file in directory.glob(pattern):
        num = number_extractor(file.name)
        if num is not None:
            if max_num is None or num > max_num:
                max_num = num

    return max_num


def filter_files_after_number(
    files: List[Path],
    threshold: int,
    number_extractor: Callable[[str], Optional[int]]
) -> List[Path]:
    """
    指定番号より大きいファイルのみをフィルタ

    Args:
        files: フィルタ対象のファイルリスト
        threshold: しきい値（この番号より大きいファイルを返す）
        number_extractor: ファイル名から番号を抽出する関数

    Returns:
        しきい値より大きい番号のファイルリスト
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
    """
    if not directory.exists():
        return 0

    return len(list(directory.glob(pattern)))
