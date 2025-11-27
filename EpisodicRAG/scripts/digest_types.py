#!/usr/bin/env python3
"""
EpisodicRAG 型定義
==================

後方互換性レイヤー - domain.types から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from domain import OverallDigestData, ShadowDigestData, LevelConfigData

    # 後方互換（従来のインポートパス）
    from digest_types import OverallDigestData, ShadowDigestData, LevelConfigData
"""

# Re-export from domain layer
from domain.types import (
    # Metadata
    BaseMetadata,
    DigestMetadata,
    # Level config
    LevelConfigData,
    # Digest data
    OverallDigestData,
    IndividualDigestData,
    ShadowLevelData,
    ShadowDigestData,
    GrandDigestLevelData,
    GrandDigestData,
    RegularDigestData,
    # Config data
    PathsConfigData,
    LevelsConfigData,
    ConfigData,
    # Times data
    DigestTimeData,
    DigestTimesData,
    # Provisional
    ProvisionalDigestEntry,
)

__all__ = [
    # Metadata
    "BaseMetadata",
    "DigestMetadata",
    # Level config
    "LevelConfigData",
    # Digest data
    "OverallDigestData",
    "IndividualDigestData",
    "ShadowLevelData",
    "ShadowDigestData",
    "GrandDigestLevelData",
    "GrandDigestData",
    "RegularDigestData",
    # Config data
    "PathsConfigData",
    "LevelsConfigData",
    "ConfigData",
    # Times data
    "DigestTimeData",
    "DigestTimesData",
    # Provisional
    "ProvisionalDigestEntry",
]
