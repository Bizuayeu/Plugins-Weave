#!/usr/bin/env python3
"""
EpisodicRAG Digest Finalizer from Shadow (Facade)
==================================================

後方互換性レイヤー - interfaces.finalize_from_shadow から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from interfaces.finalize_from_shadow import DigestFinalizerFromShadow

    # 後方互換（従来のインポートパス）
    from finalize_from_shadow import DigestFinalizerFromShadow
"""

# Interfaces層から再エクスポート
from interfaces.finalize_from_shadow import DigestFinalizerFromShadow, main

# 後方互換性：テストでpatchされる依存モジュール
from config import DigestConfig
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.tracking import DigestTimesTracker
from application.finalize import ShadowValidator, ProvisionalLoader, RegularDigestBuilder, DigestPersistence

# 後方互換性のための公開API
__all__ = [
    "DigestFinalizerFromShadow",
    "main",
    # テストでpatchされる依存モジュール
    "DigestConfig",
    "GrandDigestManager",
    "ShadowGrandDigestManager",
    "DigestTimesTracker",
    "ShadowValidator",
    "ProvisionalLoader",
    "RegularDigestBuilder",
    "DigestPersistence",
]

if __name__ == "__main__":
    main()
