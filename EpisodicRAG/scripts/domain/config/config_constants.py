#!/usr/bin/env python3
"""
Config Constants
================

設定関連の共通定数を定義。
REQUIRED_CONFIG_KEYSなど、複数のモジュールで使用される定数を一元管理。

Usage:
    from domain.config.config_constants import REQUIRED_CONFIG_KEYS, THRESHOLD_KEYS
"""


# =============================================================================
# 必須設定キー
# =============================================================================

# 設定ファイルに必須のキー
REQUIRED_CONFIG_KEYS: list[str] = ["loops_path", "digests_path", "essences_path"]

# =============================================================================
# 閾値キー
# =============================================================================

# 各レベルの閾値キー（設定ファイルで使用）
THRESHOLD_KEYS: list[str] = [
    "weekly_threshold",
    "monthly_threshold",
    "quarterly_threshold",
    "annual_threshold",
    "triennial_threshold",
    "decadal_threshold",
    "multi_decadal_threshold",
    "centurial_threshold",
]
