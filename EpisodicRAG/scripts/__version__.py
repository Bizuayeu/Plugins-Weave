#!/usr/bin/env python3
"""
EpisodicRAG バージョン定義
=========================

プロジェクト全体で使用するバージョン定数のSingle Source of Truth。
"""

# プラグインバージョン (plugin.json と同期)
__version__ = "1.1.6"

# データフォーマットバージョン (GrandDigest, ShadowGrandDigest, RegularDigest用)
# プラグインバージョンとは独立して管理
DIGEST_FORMAT_VERSION = "1.0"
