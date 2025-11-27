#!/usr/bin/env python3
"""
Provisional Loader
==================

後方互換性レイヤー - application.finalize.provisional_loader から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.finalize import ProvisionalLoader

    # 後方互換（従来のインポートパス）
    from finalize.provisional_loader import ProvisionalLoader
"""

# Application層から再エクスポート
from application.finalize.provisional_loader import ProvisionalLoader

__all__ = ["ProvisionalLoader"]
