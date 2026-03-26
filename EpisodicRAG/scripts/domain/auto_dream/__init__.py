#!/usr/bin/env python3
"""
Auto-Dream ドメイン型定義
========================

Claude Code auto-memoryファイルのスキャン結果を表現する型。

Usage:
    from domain.auto_dream import MemoryFile, AutoDreamScanResult
"""

from domain.auto_dream.types import (
    AutoDreamScanResult,
    MemoryFile,
    MemoryFileFrontmatter,
    MemoryIndex,
    MemoryType,
)

__all__ = [
    "AutoDreamScanResult",
    "MemoryFile",
    "MemoryFileFrontmatter",
    "MemoryIndex",
    "MemoryType",
]
