#!/usr/bin/env python3
"""
EpisodicRAG Provisional Digest 型定義
=====================================

Provisional Digest用TypedDict定義。
"""

from typing import List, TypedDict

from domain.types.digest import IndividualDigestData
from domain.types.metadata import DigestMetadataComplete
from domain.types.text import LongShortText


class ProvisionalDigestEntry(TypedDict):
    """
    Provisional Digest の各エントリ

    DigestAnalyzerが生成する形式。
    abstract/impressionは{long, short}形式を使用。
    """

    source_file: str
    digest_type: str
    keywords: List[str]
    abstract: LongShortText
    impression: LongShortText


class ProvisionalDigestFile(TypedDict):
    """
    Provisional Digest ファイル（_Individual.txt）の全体構造
    """

    metadata: DigestMetadataComplete
    individual_digests: List[IndividualDigestData]
