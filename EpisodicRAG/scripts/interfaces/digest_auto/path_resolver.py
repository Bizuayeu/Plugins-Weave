#!/usr/bin/env python3
"""
Digest Auto Path Resolver
=========================

設定ファイルからパスを解決するユーティリティ。

Functions:
    resolve_base_dir: base_dirを解決
    resolve_paths: loops, essences, digestsのパスを解決
"""

from pathlib import Path
from typing import Any, Dict, Tuple

__all__ = [
    "resolve_base_dir",
    "resolve_paths",
]


def resolve_base_dir(config: Dict[str, Any]) -> Path:
    """base_dirを解決

    Args:
        config: 設定データ（base_dirキーを含む）

    Returns:
        解決されたbase_dirの絶対パス

    Raises:
        ValueError: base_dirが未設定または相対パスの場合
    """
    base_dir_str = config.get("base_dir", "")
    if not base_dir_str:
        raise ValueError("base_dir is required in config.json")
    base_path = Path(base_dir_str).expanduser()
    if not base_path.is_absolute():
        raise ValueError("base_dir must be an absolute path")
    return base_path.resolve()


def resolve_paths(config: Dict[str, Any]) -> Tuple[Path, Path, Path]:
    """設定から各種パスを解決

    Args:
        config: 設定データ

    Returns:
        (loops_path, essences_path, digests_path) のタプル
    """
    base_dir = resolve_base_dir(config)
    paths = config.get("paths", {})

    loops_path = base_dir / paths.get("loops_dir", "data/Loops")
    essences_path = base_dir / paths.get("essences_dir", "data/Essences")
    digests_path = base_dir / paths.get("digests_dir", "data/Digests")

    return loops_path, essences_path, digests_path
