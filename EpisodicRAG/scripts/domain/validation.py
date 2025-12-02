#!/usr/bin/env python3
"""
Domain層 型検証ユーティリティ（リダイレクトモジュール）
======================================================

後方互換性のためのリダイレクトモジュール。
実装は domain.validators.helpers に移動。

Usage:
    from domain.validation import validate_type, collect_type_error

Note:
    新規コードでは domain.validators を直接使用することを推奨:
        from domain.validators import validate_type, collect_type_error
"""

# Re-export from domain.validators.helpers for backward compatibility
from domain.validators.helpers import collect_type_error, validate_type

__all__ = ["validate_type", "collect_type_error"]
