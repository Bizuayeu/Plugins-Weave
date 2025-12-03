#!/usr/bin/env python3
"""
EpisodicRAG Domain Validators
=============================

ドメイン層のバリデーション関数を統合。

Usage:
    from domain.validators import is_valid_overall_digest, ensure_not_none
    from domain.validators import is_valid_type, is_valid_dict, is_valid_list
    from domain.validators import validate_type, validate_list_not_empty
"""

# Digest validators
from domain.validators.digest_validators import is_valid_overall_digest

# Validation helpers (throwing validators and error collectors)
from domain.validators.helpers import (
    collect_list_element_errors,
    collect_type_error,
    validate_dict_has_keys,
    validate_dict_key_type,
    validate_list_not_empty,
    validate_type,
)

# Runtime checks
from domain.validators.runtime_checks import ensure_not_none

# Type validators (non-throwing)
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
    # type_validators (non-throwing)
    "is_valid_type",
    "get_or_default",
    "is_valid_dict",
    "is_valid_list",
    "is_valid_str",
    "is_valid_int",
    "get_dict_or_empty",
    "get_list_or_empty",
    "get_str_or_empty",
    # helpers (throwing validators)
    "validate_type",
    "validate_list_not_empty",
    "validate_dict_has_keys",
    "validate_dict_key_type",
    # helpers (error collectors)
    "collect_type_error",
    "collect_list_element_errors",
]
