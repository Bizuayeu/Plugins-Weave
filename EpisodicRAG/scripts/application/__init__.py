#!/usr/bin/env python3
"""
EpisodicRAG Application Layer
==============================

ユースケース・アプリケーションロジック層。
domain層とinfrastructure層に依存。

Subpackages:
    - validators: バリデーションユーティリティ
    - tracking: 時間追跡
    - shadow: Shadow管理
    - grand: GrandDigest管理
    - finalize: Finalize処理

Usage:
    from application import validate_dict, DigestTimesTracker
    from application.shadow import ShadowTemplate
    from application.grand import ShadowGrandDigestManager
    from application.finalize import ShadowValidator
"""

# Validators
# Finalize
from application.finalize import (
    DigestPersistence,
    ProvisionalLoader,
    RegularDigestBuilder,
    ShadowValidator,
)

# Grand
from application.grand import (
    GrandDigestManager,
    ShadowGrandDigestManager,
)

# Shadow
from application.shadow import (
    FileDetector,
    ShadowIO,
    ShadowTemplate,
    ShadowUpdater,
)

# Tracking
from application.tracking import DigestTimesTracker
from application.validators import (
    get_dict_or_default,
    get_list_or_default,
    is_valid_dict,
    is_valid_list,
    validate_dict,
    validate_list,
    validate_source_files,
)

__all__ = [
    # Validators
    "validate_dict",
    "validate_list",
    "validate_source_files",
    "is_valid_dict",
    "is_valid_list",
    "get_dict_or_default",
    "get_list_or_default",
    # Tracking
    "DigestTimesTracker",
    # Shadow
    "ShadowTemplate",
    "FileDetector",
    "ShadowIO",
    "ShadowUpdater",
    # Grand
    "GrandDigestManager",
    "ShadowGrandDigestManager",
    # Finalize
    "ShadowValidator",
    "ProvisionalLoader",
    "RegularDigestBuilder",
    "DigestPersistence",
]
