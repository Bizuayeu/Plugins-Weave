#!/usr/bin/env python3
"""
EpisodicRAG バージョン定義
=========================

後方互換性レイヤー - domain.version から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from domain import __version__, DIGEST_FORMAT_VERSION

    # 後方互換（従来のインポートパス）
    from __version__ import __version__, DIGEST_FORMAT_VERSION
"""

# Re-export from domain layer
from domain.version import __version__, DIGEST_FORMAT_VERSION

__all__ = ["__version__", "DIGEST_FORMAT_VERSION"]
