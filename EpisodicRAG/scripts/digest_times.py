#!/usr/bin/env python3
"""
Digest Times Tracker
====================

後方互換性レイヤー - application.tracking層から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.tracking import DigestTimesTracker

    # 後方互換（従来のインポートパス）
    from digest_times import DigestTimesTracker
"""

# Application層から再エクスポート
from application.tracking import DigestTimesTracker

# 後方互換性のための公開API
__all__ = [
    "DigestTimesTracker",
]
