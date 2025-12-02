#!/usr/bin/env python3
"""
EpisodicRAG レベル設定型定義
============================

レベル階層設定用TypedDict定義。
"""

from typing import Optional, TypedDict


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
