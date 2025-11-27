#!/usr/bin/env python3
"""
GrandDigest Manager
===================

後方互換性レイヤー - application.grand層から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.grand import GrandDigestManager

    # 後方互換（従来のインポートパス）
    from grand_digest import GrandDigestManager
"""

# Application層から再エクスポート
from application.grand import GrandDigestManager

# 後方互換性のための公開API
__all__ = [
    "GrandDigestManager",
]
