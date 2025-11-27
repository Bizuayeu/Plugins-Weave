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
    if not isinstance(title, str):
        raise TypeError(f"title must be str, got {type(title).__name__}")
    if max_length <= 0:
        raise ValueError(f"max_length must be positive, got {max_length}")

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
    from config import LEVEL_CONFIG, extract_file_number

    config = LEVEL_CONFIG.get(level)
    if not config:
        raise ValueError(f"Invalid level: {level}")

    prefix = config["prefix"]
    level_dir = digests_path / config["dir"]

    if not level_dir.exists():
        return 1

    # 既存ファイルから最大番号を取得
    max_num = 0
    pattern = f"{prefix}*_*.txt"

    for f in level_dir.glob(pattern):
        result = extract_file_number(f.name)
        if result and result[0] == prefix:
            max_num = max(max_num, result[1])

    return max_num + 1


__all__ = [
    "sanitize_filename",
    "get_next_digest_number",
]
