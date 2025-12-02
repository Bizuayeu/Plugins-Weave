#!/usr/bin/env python3
"""
EpisodicRAG テキスト型定義
==========================

テキストデータ用TypedDict定義。
"""

from typing import TypedDict


class LongShortText(TypedDict):
    """
    abstract/impressionの長短両形式

    DigestAnalyzerが生成する形式。
    - long: overall_digest用（2400字 / 800字）
    - short: individual_digests用（1200字 / 400字）
    """

    long: str
    short: str
