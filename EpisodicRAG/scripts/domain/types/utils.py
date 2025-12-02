#!/usr/bin/env python3
"""
EpisodicRAG 型ユーティリティ関数
================================

TypedDict操作のヘルパー関数。
"""

from typing import Any, Dict, cast


def as_dict(typed_dict: Any) -> Dict[str, Any]:
    """
    TypedDictを動的キーアクセス用にDict[str, Any]にキャスト。

    TypedDictは静的型チェックには優れるが、動的キーアクセス
    （例: data[level_name]）時にmypyが警告を出す。
    このヘルパーで意図を明確化する。

    Args:
        typed_dict: キャストするTypedDictインスタンス

    Returns:
        Dict[str, Any]としてキャストされた同じオブジェクト

    Example:
        >>> config: ConfigData = load_config()
        >>> levels = as_dict(config).get("levels", {})  # 動的アクセスOK
    """
    return cast(Dict[str, Any], typed_dict)
