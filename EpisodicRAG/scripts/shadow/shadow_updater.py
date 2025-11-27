#!/usr/bin/env python3
"""
Shadow Updater
==============

後方互換性レイヤー - application.shadow.shadow_updater から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.shadow import ShadowUpdater

    # 後方互換（従来のインポートパス）
    from shadow.shadow_updater import ShadowUpdater
"""

# Application層から再エクスポート
from application.shadow.shadow_updater import ShadowUpdater

__all__ = ["ShadowUpdater"]
