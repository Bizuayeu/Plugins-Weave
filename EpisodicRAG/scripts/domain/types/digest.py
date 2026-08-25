#!/usr/bin/env python3
"""
EpisodicRAG ダイジェストデータ型定義
====================================

Digest関連のTypedDict定義。
"""

from typing import TypedDict

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
    source_files: list[str]
    digest_type: str
    keywords: list[str]
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
    keywords: list[str]
    abstract: LongShortText
    impression: LongShortText


class ShadowLevelData(TypedDict, total=False):
    """
    ShadowGrandDigest の各レベルデータ

    Note:
        total=False により、すべてのキーがオプショナル
    """

    overall_digest: OverallDigestData | None
    individual_digests: list[IndividualDigestData]
    source_files: list[str]


class ShadowDigestData(TypedDict):
    """
    ShadowGrandDigest.txt の全体構造
    """

    metadata: DigestMetadataComplete
    latest_digests: dict[str, ShadowLevelData]


class GrandDigestLevelData(TypedDict, total=False):
    """
    GrandDigest の各レベルデータ
    """

    overall_digest: OverallDigestData | None


class GrandDigestData(TypedDict):
    """
    GrandDigest.txt の全体構造
    """

    metadata: DigestMetadataComplete
    major_digests: dict[str, GrandDigestLevelData]


class RegularDigestData(TypedDict):
    """
    Regular Digest ファイル（確定済みDigest）の構造
    """

    metadata: DigestMetadataComplete
    overall_digest: OverallDigestData
    individual_digests: list[IndividualDigestData]
