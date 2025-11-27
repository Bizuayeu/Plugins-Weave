#!/usr/bin/env python3
"""
File Detector for Shadow Updates
================================

後方互換性レイヤー - application.shadow.file_detector から再エクスポート

Usage:
    # 推奨（新しいインポートパス）
    from application.shadow import FileDetector

    # 後方互換（従来のインポートパス）
    from shadow.file_detector import FileDetector
"""

# Application層から再エクスポート
from application.shadow.file_detector import FileDetector

__all__ = ["FileDetector"]
