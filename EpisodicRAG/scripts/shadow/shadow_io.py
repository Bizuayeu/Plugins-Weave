#!/usr/bin/env python3
"""
Shadow I/O Handler
==================

後方互換性レイヤー - application.shadow.shadow_io から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.shadow import ShadowIO

    # 後方互換（従来のインポートパス）
    from shadow.shadow_io import ShadowIO
"""

# Application層から再エクスポート
from application.shadow.shadow_io import ShadowIO

__all__ = ["ShadowIO"]
