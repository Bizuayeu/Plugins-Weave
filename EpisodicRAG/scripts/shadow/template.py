#!/usr/bin/env python3
"""
Shadow Template Generator
=========================

後方互換性レイヤー - application.shadow.template から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.shadow import ShadowTemplate

    # 後方互換（従来のインポートパス）
    from shadow.template import ShadowTemplate
"""

# Application層から再エクスポート
from application.shadow.template import ShadowTemplate

__all__ = ["ShadowTemplate"]
