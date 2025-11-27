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
# Constants
from domain.constants import (
    DEFAULT_THRESHOLDS,
    LEVEL_CONFIG,
    LEVEL_NAMES,
    PLACEHOLDER_END,
    PLACEHOLDER_LIMITS,
    PLACEHOLDER_MARKER,
    PLACEHOLDER_SIMPLE,
    build_level_hierarchy,
)

# Exceptions
from domain.exceptions import (
    ConfigError,
    CorruptedDataError,
    DigestError,
    EpisodicRAGError,
    FileIOError,
    ValidationError,
)

# File naming utilities
from domain.file_naming import (
    extract_file_number,
    extract_number_only,
    extract_numbers_formatted,
    filter_files_after,
    find_max_number,
    format_digest_number,
)

# Level registry (Strategy pattern for OCP)
from domain.level_registry import (
    LevelBehavior,
    LevelMetadata,
    LevelRegistry,
    LoopLevelBehavior,
    StandardLevelBehavior,
    get_level_registry,
    reset_level_registry,
)

# Types
from domain.types import (
    # Metadata
    BaseMetadata,
    ConfigData,
    DigestMetadata,
    # Times data
    DigestTimeData,
    DigestTimesData,
    GrandDigestData,
    GrandDigestLevelData,
    IndividualDigestData,
    # Level config
    LevelConfigData,
    LevelsConfigData,
    # Digest data
    OverallDigestData,
    # Config data
    PathsConfigData,
    # Provisional
    ProvisionalDigestEntry,
    RegularDigestData,
    ShadowDigestData,
    ShadowLevelData,
)
from domain.version import DIGEST_FORMAT_VERSION, __version__

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
    "build_level_hierarchy",
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
    "find_max_number",
    "filter_files_after",
    "extract_numbers_formatted",
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
    # Level registry
    "LevelMetadata",
    "LevelBehavior",
    "StandardLevelBehavior",
    "LoopLevelBehavior",
    "LevelRegistry",
    "get_level_registry",
    "reset_level_registry",
]
