#!/usr/bin/env python3
"""
EpisodicRAG 設定データ型定義
============================

設定ファイル用TypedDict定義。
"""

from typing import Dict, List, Optional, TypedDict


class PathsConfigData(TypedDict, total=False):
    """
    config.json の paths セクション
    """

    loops_dir: str
    digests_dir: str
    essences_dir: str
    identity_file_path: Optional[str]


class LevelsConfigData(TypedDict, total=False):
    """
    config.json の levels セクション（threshold設定）
    """

    weekly_threshold: int
    monthly_threshold: int
    quarterly_threshold: int
    annual_threshold: int
    triennial_threshold: int
    decadal_threshold: int
    multi_decadal_threshold: int
    centurial_threshold: int


class ConfigData(TypedDict, total=False):
    """
    config.json の全体構造
    """

    base_dir: str
    paths: PathsConfigData
    levels: LevelsConfigData
    trusted_external_paths: List[str]


# =============================================================================
# DigestTimes の型定義
# =============================================================================


class DigestTimeData(TypedDict, total=False):
    """
    last_digest_times.json の各レベルデータ
    """

    timestamp: str
    last_processed: Optional[int]


DigestTimesData = Dict[str, DigestTimeData]
