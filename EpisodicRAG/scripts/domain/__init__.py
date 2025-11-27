#!/usr/bin/env python3
"""
EpisodicRAG Domain Layer
========================

コアビジネスロジック - 外部依存を持たない最内層。

このモジュールは以下を公開:
- 型定義 (TypedDict)
- 定数 (LEVEL_CONFIG, PLACEHOLDER_*)
- 例外クラス
- バージョン情報

Usage:
    from domain import (
        # Types
        OverallDigestData,
        ShadowDigestData,
        LevelConfigData,
        BaseMetadata,
        DigestMetadata,
        # Constants
        LEVEL_CONFIG,
        LEVEL_NAMES,
        PLACEHOLDER_LIMITS,
        PLACEHOLDER_MARKER,
        # Exceptions
        EpisodicRAGError,
        ConfigError,
        DigestError,
        ValidationError,
        FileIOError,
        CorruptedDataError,
        # Version
        __version__,
        DIGEST_FORMAT_VERSION,
    )
"""

# Version
from domain.version import __version__, DIGEST_FORMAT_VERSION

# Constants
from domain.constants import (
    LEVEL_CONFIG,
    LEVEL_NAMES,
    PLACEHOLDER_LIMITS,
    PLACEHOLDER_MARKER,
    PLACEHOLDER_END,
    PLACEHOLDER_SIMPLE,
    DEFAULT_THRESHOLDS,
)

# Exceptions
from domain.exceptions import (
    EpisodicRAGError,
    ConfigError,
    DigestError,
    ValidationError,
    FileIOError,
    CorruptedDataError,
)

# File naming utilities
from domain.file_naming import (
    extract_file_number,
    extract_number_only,
    format_digest_number,
)

# Types
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
    # Version
    "__version__",
    "DIGEST_FORMAT_VERSION",
    # Constants
    "LEVEL_CONFIG",
    "LEVEL_NAMES",
    "PLACEHOLDER_LIMITS",
    "PLACEHOLDER_MARKER",
    "PLACEHOLDER_END",
    "PLACEHOLDER_SIMPLE",
    "DEFAULT_THRESHOLDS",
    # Exceptions
    "EpisodicRAGError",
    "ConfigError",
    "DigestError",
    "ValidationError",
    "FileIOError",
    "CorruptedDataError",
    # File naming utilities
    "extract_file_number",
    "extract_number_only",
    "format_digest_number",
    # Types - Metadata
    "BaseMetadata",
    "DigestMetadata",
    # Types - Level config
    "LevelConfigData",
    # Types - Digest data
    "OverallDigestData",
    "IndividualDigestData",
    "ShadowLevelData",
    "ShadowDigestData",
    "GrandDigestLevelData",
    "GrandDigestData",
    "RegularDigestData",
    # Types - Config data
    "PathsConfigData",
    "LevelsConfigData",
    "ConfigData",
    # Types - Times data
    "DigestTimeData",
    "DigestTimesData",
    # Types - Provisional
    "ProvisionalDigestEntry",
]
