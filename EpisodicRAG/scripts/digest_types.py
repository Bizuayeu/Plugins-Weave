#!/usr/bin/env python3
"""
EpisodicRAG 型定義
==================

TypedDictを使用して、Dict[str, Any]を具体的な型に置き換え。
IDE支援とバグ検出を向上させる。

Usage:
    from digest_types import OverallDigestData, ShadowDigestData, LevelConfigData
"""
from typing import TypedDict, List, Optional, Dict, Any


# =============================================================================
# レベル設定の型定義
# =============================================================================

class LevelConfigData(TypedDict):
    """
    LEVEL_CONFIG の各レベル設定の型

    Example:
        {"prefix": "W", "digits": 4, "dir": "1_Weekly", "source": "loops", "next": "monthly"}
    """
    prefix: str
    digits: int
    dir: str
    source: str
    next: Optional[str]


# =============================================================================
# Digest データの型定義
# =============================================================================

class OverallDigestData(TypedDict):
    """
    overall_digest の構造

    Loop分析結果やDigest統合分析の共通フォーマット。
    """
    timestamp: str
    source_files: List[str]
    digest_type: str
    keywords: List[str]
    abstract: str
    impression: str


class IndividualDigestData(TypedDict):
    """
    individual_digests の各要素の構造
    """
    source_file: str
    digest_type: str
    keywords: List[str]
    abstract: str
    impression: str


class ShadowLevelData(TypedDict, total=False):
    """
    ShadowGrandDigest の各レベルデータ

    Note:
        total=False により、すべてのキーがオプショナル
    """
    overall_digest: Optional[OverallDigestData]
    individual_digests: List[IndividualDigestData]
    source_files: List[str]


class ShadowDigestData(TypedDict):
    """
    ShadowGrandDigest.txt の全体構造
    """
    metadata: Dict[str, Any]
    latest_digests: Dict[str, ShadowLevelData]


class GrandDigestLevelData(TypedDict, total=False):
    """
    GrandDigest の各レベルデータ
    """
    overall_digest: Optional[OverallDigestData]


class GrandDigestData(TypedDict):
    """
    GrandDigest.txt の全体構造
    """
    metadata: Dict[str, Any]
    major_digests: Dict[str, GrandDigestLevelData]


class RegularDigestData(TypedDict):
    """
    Regular Digest ファイル（確定済みDigest）の構造
    """
    metadata: Dict[str, Any]
    overall_digest: OverallDigestData
    individual_digests: List[IndividualDigestData]


# =============================================================================
# 設定ファイルの型定義
# =============================================================================

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


# =============================================================================
# Provisional Digest の型定義
# =============================================================================

class ProvisionalDigestEntry(TypedDict):
    """
    Provisional Digest の各エントリ
    """
    source_file: str
    digest_type: str
    keywords: List[str]
    abstract: str
    impression: str
