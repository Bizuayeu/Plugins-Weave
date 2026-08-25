#!/usr/bin/env python3
"""
EpisodicRAG レベル設定型定義
============================

レベル階層設定用TypedDict定義。
"""

from typing import TypedDict


class LevelConfigData(TypedDict):
    """
    LEVEL_CONFIG の各レベル設定の型

    Example:
        {"prefix": "W", "digits": 4, "dir": "1_Weekly", "source": "loops", "next": "monthly", "threshold": 5}

    Note:
        loop レベルは threshold: None（閾値なし、手動トリガー）
    """

    prefix: str
    digits: int
    dir: str
    source: str
    next: str | None
    threshold: int | None  # loop レベルは None


class LevelHierarchyEntry(TypedDict):
    """
    レベル階層エントリの型（ShadowUpdater用）

    Example:
        {"source": "loops", "next": "monthly"}
    """

    source: str
    next: str | None
