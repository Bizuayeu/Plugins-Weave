#!/usr/bin/env python3
"""
Utility Functions
=================

後方互換性レイヤー - infrastructure層から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from infrastructure import load_json, save_json, log_info

    # 後方互換（従来のインポートパス）
    from utils import load_json_with_template, save_json, log_info
"""
import re
from pathlib import Path
from typing import Optional, Callable, Dict, Any

# Infrastructure層から再エクスポート
from infrastructure.json_repository import (
    load_json_with_template,
    save_json,
)
from infrastructure.logging_config import (
    logger,
    log_error,
    log_warning,
    log_info,
)


# =============================================================================
# ファイル名処理（utils固有 - infrastructure層に移動しない）
# =============================================================================


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


# =============================================================================
# Digest番号操作（utils固有 - infrastructure層に移動しない）
# =============================================================================


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


# 後方互換性のための公開API
__all__ = [
    # Logging
    "logger",
    "log_error",
    "log_warning",
    "log_info",
    # JSON
    "load_json_with_template",
    "save_json",
    # Filename
    "sanitize_filename",
    # Digest number
    "get_next_digest_number",
]
