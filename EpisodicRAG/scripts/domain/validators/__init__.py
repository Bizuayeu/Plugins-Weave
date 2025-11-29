#!/usr/bin/env python3
"""
EpisodicRAG Domain Validators
=============================

ドメイン層のバリデーション関数。
外部依存を持たない純粋な検証ロジック。

Usage:
    from domain.validators import is_valid_overall_digest, ensure_not_none
    from domain.validators import is_valid_type, is_valid_dict, is_valid_list
"""

from domain.validators.digest_validators import is_valid_overall_digest
from domain.validators.runtime_checks import ensure_not_none
from domain.validators.type_validators import (
    get_dict_or_empty,
    get_list_or_empty,
    get_or_default,
    get_str_or_empty,
    is_valid_dict,
    is_valid_int,
    is_valid_list,
    is_valid_str,
    is_valid_type,
)

__all__ = [
    # digest_validators
    "is_valid_overall_digest",
    # runtime_checks
    "ensure_not_none",
    # type_validators
    "is_valid_type",
    "get_or_default",
    "is_valid_dict",
    "is_valid_list",
    "is_valid_str",
    "is_valid_int",
    "get_dict_or_empty",
    "get_list_or_empty",
    "get_str_or_empty",
]
