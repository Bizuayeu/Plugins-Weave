#!/usr/bin/env python3
"""
EpisodicRAG 型定義パッケージ
============================

TypedDictを使用して、Dict[str, Any]を具体的な型に置き換え。
IDE支援とバグ検出を向上させる。

Usage:
    from domain.types import OverallDigestData, ShadowDigestData, LevelConfigData

Note:
    後方互換性のため、すべての型はこの __init__.py から直接インポート可能。
    `from domain.types import ConfigData` は引き続き動作する。
"""

# Metadata types
from domain.types.metadata import (
    BaseMetadata,
    DigestMetadata,
    DigestMetadataComplete,
)

# Level types
from domain.types.level import (
    LevelConfigData,
    LevelHierarchyEntry,
)

# Text types
from domain.types.text import (
    LongShortText,
)

# Digest types
from domain.types.digest import (
    OverallDigestData,
    IndividualDigestData,
    ShadowLevelData,
    ShadowDigestData,
    GrandDigestLevelData,
    GrandDigestData,
    RegularDigestData,
)

# Config types
from domain.types.config import (
    PathsConfigData,
    LevelsConfigData,
    ConfigData,
    DigestTimeData,
    DigestTimesData,
)

# Entry types (Provisional)
from domain.types.entry import (
    ProvisionalDigestEntry,
    ProvisionalDigestFile,
)

# Utility functions
from domain.types.utils import (
    as_dict,
)

# TypeGuard functions
from domain.types.guards import (
    is_config_data,
    is_level_config_data,
    is_shadow_digest_data,
    is_long_short_text,
)

__all__ = [
    # Metadata
    "BaseMetadata",
    "DigestMetadata",
    "DigestMetadataComplete",
    # Level
    "LevelConfigData",
    "LevelHierarchyEntry",
    # Text
    "LongShortText",
    # Digest
    "OverallDigestData",
    "IndividualDigestData",
    "ShadowLevelData",
    "ShadowDigestData",
    "GrandDigestLevelData",
    "GrandDigestData",
    "RegularDigestData",
    # Config
    "PathsConfigData",
    "LevelsConfigData",
    "ConfigData",
    "DigestTimeData",
    "DigestTimesData",
    # Entry (Provisional)
    "ProvisionalDigestEntry",
    "ProvisionalDigestFile",
    # Utils
    "as_dict",
    # Guards
    "is_config_data",
    "is_level_config_data",
    "is_shadow_digest_data",
    "is_long_short_text",
]
