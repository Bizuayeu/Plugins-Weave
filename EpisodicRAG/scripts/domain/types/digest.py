#!/usr/bin/env python3
"""
EpisodicRAG ダイジェストデータ型定義
====================================

Digest関連のTypedDict定義。
"""

from typing import Dict, List, Optional, TypedDict

from domain.types.metadata import DigestMetadataComplete
from domain.types.text import LongShortText


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

    DigestAnalyzerが生成する形式。
    abstract/impressionは{long, short}形式を使用。
    """

    source_file: str
    digest_type: str
    keywords: List[str]
    abstract: LongShortText
    impression: LongShortText


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
