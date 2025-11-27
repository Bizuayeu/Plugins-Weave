#!/usr/bin/env python3
"""
Digest Persistence
==================

後方互換性レイヤー - application.finalize.persistence から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.finalize import DigestPersistence

    # 後方互換（従来のインポートパス）
    from finalize.persistence import DigestPersistence
"""

# Application層から再エクスポート
from application.finalize.persistence import DigestPersistence

__all__ = ["DigestPersistence"]
