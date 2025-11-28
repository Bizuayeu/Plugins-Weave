#!/usr/bin/env python3
"""
Interface Helper Functions
==========================

Interfaces層で使用するヘルパー関数。

- sanitize_filename: ファイル名のサニタイズ
- get_next_digest_number: 次のDigest番号を取得
"""

import re
from pathlib import Path
from typing import List, Union

from domain.error_formatter import get_error_formatter
from domain.exceptions import ConfigError, ValidationError


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """
    ファイル名として安全な文字列に変換

    Args:
        title: 元のタイトル文字列
        max_length: 最大文字数（デフォルト: 50）

    Returns:
        ファイル名として安全な文字列（空の場合は"untitled"）

    Raises:
        TypeError: titleがstr型でない場合
        ValueError: max_lengthが正の整数でない場合
    """
    # 型チェック
    formatter = get_error_formatter()
    if not isinstance(title, str):
        raise ValidationError(formatter.validation.invalid_type("title", "str", title))
    if max_length <= 0:
        raise ValidationError(formatter.validation.validation_error("max_length", "must be positive", max_length))

    # 危険な文字を削除
    sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
    # 空白をアンダースコアに変換
    sanitized = re.sub(r'\s+', '_', sanitized)
    # 先頭・末尾のアンダースコアを削除
    sanitized = sanitized.strip('_')
    # 長さ制限
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')

    # 結果が空の場合
    if not sanitized:
        return "untitled"

    return sanitized


def get_next_digest_number(digests_path: Path, level: str) -> int:
    """
    指定レベルの次のDigest番号を取得。

    既存のRegularDigestファイルをスキャンし、最大番号+1を返す。
    ファイルが存在しない場合は1を返す。

    Args:
        digests_path: Digestsディレクトリのパス
        level: Digestレベル（weekly, monthly, quarterly, annual,
               triennial, decadal, multi_decadal, centurial）

    Returns:
        次の番号（1始まり）

    Raises:
        ValueError: 無効なlevelが指定された場合
    """
    # 循環インポートを避けるためローカルインポート
    from domain.constants import LEVEL_CONFIG
    from domain.file_naming import find_max_number

    config = LEVEL_CONFIG.get(level)
    if not config:
        formatter = get_error_formatter()
        raise ConfigError(formatter.config.invalid_level(level, list(LEVEL_CONFIG.keys())))

    prefix = str(config["prefix"])
    level_dir = digests_path / str(config["dir"])

    if not level_dir.exists():
        return 1

    # 統一関数を使用して最大番号を取得
    pattern = f"{prefix}*_*.txt"
    existing_files = list(level_dir.glob(pattern))
    # Cast to List[Path | str] for find_max_number compatibility
    files_for_search: List[Union[Path, str]] = list(existing_files)
    max_num = find_max_number(files_for_search, prefix)

    return (max_num or 0) + 1


__all__ = [
    "sanitize_filename",
    "get_next_digest_number",
]
