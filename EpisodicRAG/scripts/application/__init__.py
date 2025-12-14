#!/usr/bin/env python3
"""
EpisodicRAG Application Layer
==============================

ユースケース・アプリケーションロジック層。
domain層とinfrastructure層に依存。

Subpackages:
    - tracking: 時間追跡
    - shadow: Shadow管理
    - grand: GrandDigest管理
    - finalize: Finalize処理

Usage:
    from application import DigestTimesTracker
    from application.shadow import ShadowTemplate
    from application.grand import ShadowGrandDigestManager
    from application.finalize import ShadowValidator

Note:
    バリデーション関数は domain.validators から直接インポートしてください:
    from domain.validators import is_valid_dict, is_valid_list, validate_type
"""

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

__all__ = [
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
