#!/usr/bin/env python3
"""
EpisodicRAG Literal Type Definitions
====================================

Literal型を使用して、文字列リテラルに型安全性を追加。
IDE補完とmypy検査を向上させる。

Usage:
    from domain.types import LevelName, AllLevelName, LevelConfigKey

Note:
    すべてのLiteral型は domain.types から直接インポート可能。
"""

from typing import Literal

# =============================================================================
# Level Names
# =============================================================================

# 8階層レベル名（loop除く）
LevelName = Literal[
    "weekly",
    "monthly",
    "quarterly",
    "annual",
    "triennial",
    "decadal",
    "multi_decadal",
    "centurial",
]

# Loop含む全レベル名
AllLevelName = Literal[
    "loop",
    "weekly",
    "monthly",
    "quarterly",
    "annual",
    "triennial",
    "decadal",
    "multi_decadal",
    "centurial",
]

# =============================================================================
# Level Configuration Keys
# =============================================================================

# LEVEL_CONFIG辞書のキー
LevelConfigKey = Literal["prefix", "digits", "dir", "source", "next", "threshold"]

# =============================================================================
# Source Types
# =============================================================================

# ソースタイプ（各レベルの入力元）
SourceType = Literal[
    "loops",
    "weekly",
    "monthly",
    "quarterly",
    "annual",
    "triennial",
    "decadal",
    "multi_decadal",
]

# =============================================================================
# File Suffixes
# =============================================================================

# Provisionalダイジェストのサフィックス
ProvisionalSuffix = Literal["_Individual.txt", "_Overall.txt"]

# =============================================================================
# Configuration Keys
# =============================================================================

# パス設定キー
PathConfigKey = Literal[
    "loops_path",
    "digests_path",
    "essences_path",
    "base_dir",
    "identity_file",
]

# 閾値設定キー
ThresholdKey = Literal[
    "weekly_threshold",
    "monthly_threshold",
    "quarterly_threshold",
    "annual_threshold",
    "triennial_threshold",
    "decadal_threshold",
    "multi_decadal_threshold",
    "centurial_threshold",
]

# =============================================================================
# Log Prefixes
# =============================================================================

# デバッグログプレフィックス
LogPrefix = Literal["[STATE]", "[FILE]", "[VALIDATE]", "[DECISION]"]

# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Level names
    "LevelName",
    "AllLevelName",
    # Config keys
    "LevelConfigKey",
    # Source types
    "SourceType",
    # File suffixes
    "ProvisionalSuffix",
    # Path config keys
    "PathConfigKey",
    "ThresholdKey",
    # Log prefixes
    "LogPrefix",
]
