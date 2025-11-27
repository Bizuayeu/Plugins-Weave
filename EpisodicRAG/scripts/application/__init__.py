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
from application.validators import (
    validate_dict,
    validate_list,
    validate_source_files,
    is_valid_dict,
    is_valid_list,
    get_dict_or_default,
    get_list_or_default,
)

# Tracking
from application.tracking import DigestTimesTracker

# Shadow
from application.shadow import (
    ShadowTemplate,
    FileDetector,
    ShadowIO,
    ShadowUpdater,
)

# Grand
from application.grand import (
    GrandDigestManager,
    ShadowGrandDigestManager,
)

# Finalize
from application.finalize import (
    ShadowValidator,
    ProvisionalLoader,
    RegularDigestBuilder,
    DigestPersistence,
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
