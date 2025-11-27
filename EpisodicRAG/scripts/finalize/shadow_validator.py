#!/usr/bin/env python3
"""
Shadow Validator
================

後方互換性レイヤー - application.finalize.shadow_validator から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.finalize import ShadowValidator

    # 後方互換（従来のインポートパス）
    from finalize.shadow_validator import ShadowValidator
"""

# Application層から再エクスポート
from application.finalize.shadow_validator import ShadowValidator

__all__ = ["ShadowValidator"]
