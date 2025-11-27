#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ProvisionalDigest保存スクリプト

後方互換性レイヤー - interfaces.save_provisional_digest から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from interfaces.save_provisional_digest import ProvisionalDigestSaver

    # 後方互換（従来のインポートパス）
    from save_provisional_digest import ProvisionalDigestSaver
"""

# Interfaces層から再エクスポート
from interfaces.save_provisional_digest import ProvisionalDigestSaver, main

# 後方互換性：テストでpatchされる依存モジュール
from config import DigestConfig

# 後方互換性のための公開API
__all__ = [
    "ProvisionalDigestSaver",
    "main",
    "DigestConfig",
]

if __name__ == "__main__":
    main()
