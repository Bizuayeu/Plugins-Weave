#!/usr/bin/env python3
"""
EpisodicRAG メタデータ型定義
============================

ダイジェストファイルのメタデータ用TypedDict定義。
"""

from typing import TypedDict


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
