#!/usr/bin/env python3
"""
EpisodicRAG バリデーションユーティリティ
========================================

後方互換性レイヤー - application層から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.validators import validate_dict, validate_list

    # 後方互換（従来のインポートパス）
    from validators import validate_dict, validate_list
"""

# Application層から再エクスポート
from application.validators import (
    validate_dict,
    validate_list,
    validate_source_files,
    is_valid_dict,
    is_valid_list,
    get_dict_or_default,
    get_list_or_default,
)

# 後方互換性のための公開API
__all__ = [
    "validate_dict",
    "validate_list",
    "validate_source_files",
    "is_valid_dict",
    "is_valid_list",
    "get_dict_or_default",
    "get_list_or_default",
]
