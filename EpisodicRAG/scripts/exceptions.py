#!/usr/bin/env python3
"""
EpisodicRAG カスタム例外
========================

後方互換性レイヤー - domain.exceptions から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from domain import ConfigError, DigestError, ValidationError, FileIOError

    # 後方互換（従来のインポートパス）
    from exceptions import ConfigError, DigestError, ValidationError, FileIOError
"""

# Re-export from domain layer
from domain.exceptions import (
    EpisodicRAGError,
    ConfigError,
    DigestError,
    ValidationError,
    FileIOError,
    CorruptedDataError,
)

__all__ = [
    "EpisodicRAGError",
    "ConfigError",
    "DigestError",
    "ValidationError",
    "FileIOError",
    "CorruptedDataError",
]
