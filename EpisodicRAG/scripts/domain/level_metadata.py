#!/usr/bin/env python3
"""
Level Metadata - Immutable Level Properties
============================================

レベルの不変プロパティを定義するdataclass。

Attributes:
    name: レベル名（例: "weekly", "monthly"）
    prefix: ファイル名プレフィックス（例: "W", "M", "Loop"）
    digits: 番号の桁数（例: 4 -> W0001）
    dir: digests_path以下のサブディレクトリ名
    source: この階層を生成する際の入力元
    next_level: 確定時にカスケードする上位階層（None = 最上位）

Usage:
    from domain.level_metadata import LevelMetadata

    metadata = LevelMetadata(
        name="weekly",
        prefix="W",
        digits=4,
        dir="1_Weekly",
        source="loops",
        next_level="monthly"
    )

Architecture:
    - SRP準拠: レベルの静的プロパティのみを担当
    - Immutable: frozen=True で不変性を保証
    - level_behaviors.py と level_registry.py から使用される
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelMetadata:
    """
    レベルの不変プロパティ

    Attributes:
        name: レベル名（例: "weekly", "monthly"）
        prefix: ファイル名プレフィックス（例: "W", "M", "Loop"）
        digits: 番号の桁数（例: 4 -> W0001）
        dir: digests_path以下のサブディレクトリ名
        source: この階層を生成する際の入力元
        next_level: 確定時にカスケードする上位階層（None = 最上位）

    Example:
        >>> metadata = LevelMetadata(
        ...     name="weekly",
        ...     prefix="W",
        ...     digits=4,
        ...     dir="1_Weekly",
        ...     source="loops",
        ...     next_level="monthly"
        ... )
        >>> metadata.prefix
        'W'
    """

    name: str
    prefix: str
    digits: int
    dir: str
    source: str
    next_level: str | None
