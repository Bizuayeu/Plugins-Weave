#!/usr/bin/env python3
"""
Threshold Provider
==================

しきい値管理
"""

from domain.constants import DEFAULT_THRESHOLDS, LEVEL_CONFIG, LEVEL_NAMES
from domain.exceptions import ConfigError
from domain.types import ConfigData, as_dict

__all__ = ["ThresholdProvider"]


class ThresholdProvider:
    """しきい値プロバイダー

    明示的プロパティでIDE補完をサポート:
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

    # =========================================================================
    # 明示的プロパティ（IDE補完対応）
    # =========================================================================

    @property
    def weekly_threshold(self) -> int:
        """週次thresholdを取得"""
        return self.get_threshold("weekly")

    @property
    def monthly_threshold(self) -> int:
        """月次thresholdを取得"""
        return self.get_threshold("monthly")

    @property
    def quarterly_threshold(self) -> int:
        """四半期thresholdを取得"""
        return self.get_threshold("quarterly")

    @property
    def annual_threshold(self) -> int:
        """年次thresholdを取得"""
        return self.get_threshold("annual")

    @property
    def triennial_threshold(self) -> int:
        """3年thresholdを取得"""
        return self.get_threshold("triennial")

    @property
    def decadal_threshold(self) -> int:
        """10年thresholdを取得"""
        return self.get_threshold("decadal")

    @property
    def multi_decadal_threshold(self) -> int:
        """数十年thresholdを取得"""
        return self.get_threshold("multi_decadal")

    @property
    def centurial_threshold(self) -> int:
        """100年thresholdを取得"""
        return self.get_threshold("centurial")
