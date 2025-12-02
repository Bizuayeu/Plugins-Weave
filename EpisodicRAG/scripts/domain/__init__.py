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
    LEVEL_CONFIG,
    LEVEL_NAMES,
    PLACEHOLDER_END,
    PLACEHOLDER_LIMITS,
    PLACEHOLDER_MARKER,
    PLACEHOLDER_SIMPLE,
    build_level_hierarchy,
)

# File constants
from domain.file_constants import (
    CONFIG_FILENAME,
    CONFIG_TEMPLATE,
    DATA_DIR_NAME,
    DIGEST_TIMES_FILENAME,
    DIGEST_TIMES_TEMPLATE,
    ESSENCES_DIR_NAME,
    GRAND_DIGEST_FILENAME,
    GRAND_DIGEST_TEMPLATE,
    INDIVIDUAL_DIGEST_SUFFIX,
    LOOP_FILE_PATTERN,
    LOOPS_DIR_NAME,
    MONTHLY_FILE_PATTERN,
    OVERALL_DIGEST_SUFFIX,
    PLUGIN_CONFIG_DIR,
    PROVISIONALS_SUBDIR,
    SHADOW_GRAND_DIGEST_FILENAME,
    SHADOW_GRAND_DIGEST_TEMPLATE,
    WEEKLY_FILE_PATTERN,
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
# Note: LevelMetadata and LevelBehavior are defined in separate files for SRP
# but re-exported from level_registry for backward compatibility
from domain.level_behaviors import (
    LevelBehavior,
    LoopLevelBehavior,
    StandardLevelBehavior,
)
from domain.level_metadata import LevelMetadata
from domain.level_registry import (
    LevelRegistry,
    get_level_registry,
    reset_level_registry,
)

# Text utilities
from domain.text_utils import (
    extract_long_value,
    extract_short_value,
    extract_value,
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
    # Long/Short text type
    is_long_short_text,
    # Level config
    LevelConfigData,
    LevelsConfigData,
    LongShortText,
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

# Domain validators (digest validation, runtime checks)
from domain.validators import ensure_not_none, is_valid_overall_digest

# Validation helpers (SSoT)
from domain.validation_helpers import (
    collect_list_element_errors,
    validate_dict_has_keys,
    validate_dict_key_type,
    validate_list_not_empty,
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
    "build_level_hierarchy",
    # File constants
    "GRAND_DIGEST_FILENAME",
    "SHADOW_GRAND_DIGEST_FILENAME",
    "GRAND_DIGEST_TEMPLATE",
    "SHADOW_GRAND_DIGEST_TEMPLATE",
    "DIGEST_TIMES_TEMPLATE",
    "CONFIG_TEMPLATE",
    "CONFIG_FILENAME",
    "DIGEST_TIMES_FILENAME",
    "PLUGIN_CONFIG_DIR",
    "ESSENCES_DIR_NAME",
    "LOOPS_DIR_NAME",
    "PROVISIONALS_SUBDIR",
    "DATA_DIR_NAME",
    "LOOP_FILE_PATTERN",
    "WEEKLY_FILE_PATTERN",
    "MONTHLY_FILE_PATTERN",
    "INDIVIDUAL_DIGEST_SUFFIX",
    "OVERALL_DIGEST_SUFFIX",
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
    # Types - LongShortText
    "LongShortText",
    "is_long_short_text",
    # Text utilities
    "extract_long_value",
    "extract_short_value",
    "extract_value",
    # Level registry
    "LevelMetadata",
    "LevelBehavior",
    "StandardLevelBehavior",
    "LoopLevelBehavior",
    "LevelRegistry",
    "get_level_registry",
    "reset_level_registry",
    # Domain validators
    "is_valid_overall_digest",
    "ensure_not_none",
    # Validation helpers
    "validate_list_not_empty",
    "validate_dict_has_keys",
    "validate_dict_key_type",
    "collect_list_element_errors",
]
