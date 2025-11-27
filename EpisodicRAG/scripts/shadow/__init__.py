"""
Shadow Package - ShadowGrandDigest management components
=========================================================

後方互換性レイヤー - application.shadow層から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.shadow import ShadowTemplate, FileDetector, ShadowIO, ShadowUpdater

    # 後方互換（従来のインポートパス）
    from shadow import ShadowTemplate, FileDetector, ShadowIO, ShadowUpdater
"""

# Application層から再エクスポート
from application.shadow import (
    ShadowTemplate,
    FileDetector,
    ShadowIO,
    ShadowUpdater,
)

__all__ = [
    "ShadowTemplate",
    "FileDetector",
    "ShadowIO",
    "ShadowUpdater",
]
