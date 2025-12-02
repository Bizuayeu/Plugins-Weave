#!/usr/bin/env python3
"""
統一バリデーションヘルパー（リダイレクトモジュール）
==================================================

後方互換性のためのリダイレクトモジュール。
実装は domain.validators.helpers に移動。

Usage:
    from domain.validation_helpers import (
        validate_list_not_empty,
        validate_dict_has_keys,
        validate_dict_key_type,
        collect_list_element_errors,
    )

Note:
    新規コードでは domain.validators を直接使用することを推奨:
        from domain.validators import validate_list_not_empty, validate_dict_has_keys
"""

# Re-export from domain.validators.helpers for backward compatibility
from domain.validators.helpers import (
    collect_list_element_errors,
    validate_dict_has_keys,
    validate_dict_key_type,
    validate_list_not_empty,
)

__all__ = [
    "validate_list_not_empty",
    "validate_dict_has_keys",
    "validate_dict_key_type",
    "collect_list_element_errors",
]
