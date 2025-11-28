#!/usr/bin/env python3
"""
EpisodicRAG 型定義
==================

TypedDictを使用して、Dict[str, Any]を具体的な型に置き換え。
IDE支援とバグ検出を向上させる。

Usage:
    from domain.types import OverallDigestData, ShadowDigestData, LevelConfigData
"""

from typing import Any, Dict, List, Optional, TypedDict, cast

# =============================================================================
# メタデータ型定義
# =============================================================================


class BaseMetadata(TypedDict, total=False):
    """
    共通メタデータフィールド

    すべてのダイジェストファイルで使用される基本メタデータ。
    """

    version: str
    last_updated: str


class DigestMetadata(BaseMetadata, total=False):
    """
    ダイジェスト固有のメタデータ

    RegularDigest や GrandDigest で使用。
    """

    digest_level: str
    digest_number: str
    source_count: int


class DigestMetadataComplete(BaseMetadata, total=False):
    """
    ダイジェストファイルの完全なメタデータ

    すべてのダイジェストファイルで使用される統一メタデータ型。
    Dict[str, Any] の置き換え用。

    Note: version, last_updated are inherited from BaseMetadata
    """

    digest_level: str
    digest_number: str
    source_count: int
    description: str


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


class LevelHierarchyEntry(TypedDict):
    """
    レベル階層エントリの型（ShadowUpdater用）

    Example:
        {"source": "loops", "next": "monthly"}
    """

    source: str
    next: Optional[str]


# =============================================================================
# Digest データの型定義
# =============================================================================


class OverallDigestData(TypedDict, total=False):
    """
    overall_digest の構造

    Loop分析結果やDigest統合分析の共通フォーマット。
    Note: total=False allows optional fields (name is only used in RegularDigest)
    """

    name: str
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

    metadata: DigestMetadataComplete
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

    metadata: DigestMetadataComplete
    major_digests: Dict[str, GrandDigestLevelData]


class RegularDigestData(TypedDict):
    """
    Regular Digest ファイル（確定済みDigest）の構造
    """

    metadata: DigestMetadataComplete
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


class ProvisionalDigestFile(TypedDict):
    """
    Provisional Digest ファイル（_Individual.txt）の全体構造
    """

    metadata: DigestMetadataComplete
    individual_digests: List[IndividualDigestData]


# =============================================================================
# 型ユーティリティ関数
# =============================================================================


def as_dict(typed_dict: Any) -> Dict[str, Any]:
    """
    TypedDictを動的キーアクセス用にDict[str, Any]にキャスト。

    TypedDictは静的型チェックには優れるが、動的キーアクセス
    （例: data[level_name]）時にmypyが警告を出す。
    このヘルパーで意図を明確化する。

    Args:
        typed_dict: キャストするTypedDictインスタンス

    Returns:
        Dict[str, Any]としてキャストされた同じオブジェクト

    Example:
        >>> config: ConfigData = load_config()
        >>> levels = as_dict(config).get("levels", {})  # 動的アクセスOK
    """
    return cast(Dict[str, Any], typed_dict)
