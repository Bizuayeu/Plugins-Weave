#!/usr/bin/env python3
"""
Threshold Provider
==================

しきい値管理
"""

from typing import Any, Dict

from domain.constants import DEFAULT_THRESHOLDS, LEVEL_CONFIG, LEVEL_NAMES
from domain.exceptions import ConfigError


class ThresholdProvider:
    """しきい値プロバイダー"""

    def __init__(self, config: Dict[str, Any]):
        """
        初期化

        Args:
            config: 設定辞書
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
        return self.config.get("levels", {}).get(key, DEFAULT_THRESHOLDS.get(level, 5))

    @property
    def weekly_threshold(self) -> int:
        """Weekly生成に必要なLoop数"""
        return self.get_threshold("weekly")

    @property
    def monthly_threshold(self) -> int:
        """Monthly生成に必要なWeekly数"""
        return self.get_threshold("monthly")

    @property
    def quarterly_threshold(self) -> int:
        """Quarterly生成に必要なMonthly数"""
        return self.get_threshold("quarterly")

    @property
    def annual_threshold(self) -> int:
        """Annual生成に必要なQuarterly数"""
        return self.get_threshold("annual")

    @property
    def triennial_threshold(self) -> int:
        """Triennial生成に必要なAnnual数"""
        return self.get_threshold("triennial")

    @property
    def decadal_threshold(self) -> int:
        """Decadal生成に必要なTriennial数"""
        return self.get_threshold("decadal")

    @property
    def multi_decadal_threshold(self) -> int:
        """Multi-decadal生成に必要なDecadal数"""
        return self.get_threshold("multi_decadal")

    @property
    def centurial_threshold(self) -> int:
        """Centurial生成に必要なMulti-decadal数"""
        return self.get_threshold("centurial")
