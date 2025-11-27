#!/usr/bin/env python3
"""
Digest Builder
==============

後方互換性レイヤー - application.finalize.digest_builder から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.finalize import RegularDigestBuilder

    # 後方互換（従来のインポートパス）
    from finalize.digest_builder import RegularDigestBuilder
"""

# Application層から再エクスポート
from application.finalize.digest_builder import RegularDigestBuilder

__all__ = ["RegularDigestBuilder"]
