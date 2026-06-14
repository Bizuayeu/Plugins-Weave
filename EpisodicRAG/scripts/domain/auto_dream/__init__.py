#!/usr/bin/env python3
"""
Auto-Dream ドメイン型定義
========================

Claude Code auto-memoryファイルのスキャン結果を表現する型。

Usage:
    from domain.auto_dream import MemoryFile, AutoDreamScanResult
"""

from domain.auto_dream.defrag_types import (
    DEFRAG_THRESHOLD,
    VALID_DEFRAG_KINDS,
    DefragCandidate,
    DefragKind,
    DefragScanResult,
)
from domain.auto_dream.types import (
    AutoDreamScanResult,
    MemoryFile,
    MemoryFileFrontmatter,
    MemoryIndex,
    MemoryType,
)

__all__ = [
    # types.py（足す dream＝auto_dream_scan）
    "AutoDreamScanResult",
    "MemoryFile",
    "MemoryFileFrontmatter",
    "MemoryIndex",
    "MemoryType",
    # defrag_types.py（引く dream＝dream-defrag）
    "DEFRAG_THRESHOLD",
    "VALID_DEFRAG_KINDS",
    "DefragCandidate",
    "DefragKind",
    "DefragScanResult",
]
