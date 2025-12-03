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
# Config types
from domain.types.config import (
    ConfigData,
    DigestTimeData,
    DigestTimesData,
    LevelsConfigData,
    PathsConfigData,
)

# Digest types
from domain.types.digest import (
    GrandDigestData,
    GrandDigestLevelData,
    IndividualDigestData,
    OverallDigestData,
    RegularDigestData,
    ShadowDigestData,
    ShadowLevelData,
)

# Entry types (Provisional)
from domain.types.entry import (
    ProvisionalDigestEntry,
    ProvisionalDigestFile,
)

# TypeGuard functions
from domain.types.guards import (
    is_config_data,
    is_level_config_data,
    is_long_short_text,
    is_shadow_digest_data,
)

# Level types
from domain.types.level import (
    LevelConfigData,
    LevelHierarchyEntry,
)

# Literal types
from domain.types.level_literals import (
    AllLevelName,
    LevelConfigKey,
    LevelName,
    LogPrefix,
    PathConfigKey,
    ProvisionalSuffix,
    SourceType,
    ThresholdKey,
)
from domain.types.metadata import (
    BaseMetadata,
    DigestMetadata,
    DigestMetadataComplete,
)

# Text types
from domain.types.text import (
    LongShortText,
)

# Utility functions
from domain.types.utils import (
    as_dict,
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
    # Literal types
    "LevelName",
    "AllLevelName",
    "LevelConfigKey",
    "SourceType",
    "ProvisionalSuffix",
    "PathConfigKey",
    "ThresholdKey",
    "LogPrefix",
]
