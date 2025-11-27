#!/usr/bin/env python3
"""
ShadowGrandDigest Manager (Facade)
===================================

後方互換性レイヤー - application.grand層から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.grand import ShadowGrandDigestManager

    # 後方互換（従来のインポートパス）
    from shadow_grand_digest import ShadowGrandDigestManager
"""

# Application層から再エクスポート
from application.grand import ShadowGrandDigestManager

# main関数も再エクスポート
from application.grand.shadow_grand_digest import main

# 後方互換性：テストでpatchされる依存モジュール
from config import DigestConfig
from application.tracking import DigestTimesTracker

# 後方互換性のための公開API
__all__ = [
    "ShadowGrandDigestManager",
    "DigestConfig",
    "DigestTimesTracker",
    "main",
]

if __name__ == "__main__":
    main()
