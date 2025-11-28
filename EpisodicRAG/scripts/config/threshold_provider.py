#!/usr/bin/env python3
"""
Threshold Provider
==================

しきい値管理
"""

from typing import Any, Dict, cast

from domain.constants import DEFAULT_THRESHOLDS, LEVEL_CONFIG, LEVEL_NAMES
from domain.exceptions import ConfigError
from domain.types import ConfigData, as_dict

__all__ = ["ThresholdProvider"]


class ThresholdProvider:
    """しきい値プロバイダー

    動的プロパティアクセスをサポート:
        - weekly_threshold
        - monthly_threshold
        - quarterly_threshold
        - annual_threshold
        - triennial_threshold
        - decadal_threshold
        - multi_decadal_threshold
        - centurial_threshold
    """

    def __init__(self, config: ConfigData):
        """
        初期化

        Args:
            config: 設定辞書（ConfigData型）
        """
        self.config = config

    def get_threshold(self, level: str) -> int:
        """
        指定レベルのthresholdを動的に取得

        Args:
            level: 階層名（weekly, monthly, quarterly, annual, triennial, decadal, multi_decadal, centurial）

        Returns:
            そのレベルのthreshold値

        Raises:
            ConfigError: 不正なレベル名の場合
        """
        if level not in LEVEL_CONFIG:
            raise ConfigError(f"Invalid level: {level}. Valid levels: {LEVEL_NAMES}")

        key = f"{level}_threshold"
        default = DEFAULT_THRESHOLDS.get(level, 5)
        # Cast to Dict for dynamic key access
        levels_dict = as_dict(self.config.get("levels", {}))
        if key in levels_dict:
            value = levels_dict[key]
            return int(value) if isinstance(value, (int, str, float)) else default
        return default

    def __getattr__(self, name: str) -> Any:
        """
        動的なthresholdプロパティアクセス

        例: provider.weekly_threshold -> get_threshold("weekly")

        Args:
            name: アトリビュート名

        Returns:
            threshold値

        Raises:
            AttributeError: 無効なアトリビュート名の場合
        """
        if name.endswith("_threshold"):
            level = name[:-10]  # "_threshold" を除去
            if level in LEVEL_NAMES:
                return self.get_threshold(level)
        raise AttributeError(f"'{type(self).__name__}' has no attribute '{name}'")
