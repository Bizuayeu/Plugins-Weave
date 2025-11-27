#!/usr/bin/env python3
"""
Shadow Template Generator
=========================

ShadowGrandDigestのテンプレートとプレースホルダー生成を担当
"""

from datetime import datetime
from typing import Dict, Any, List

from config import (
    PLACEHOLDER_LIMITS,
    PLACEHOLDER_MARKER,
    PLACEHOLDER_END,
    PLACEHOLDER_SIMPLE,
)
from __version__ import DIGEST_FORMAT_VERSION


class ShadowTemplate:
    """ShadowGrandDigestテンプレート生成クラス"""

    def __init__(self, levels: List[str]):
        """
        初期化

        Args:
            levels: レベル名のリスト（例: ["weekly", "monthly", ...]）
        """
        self.levels = levels

    def create_empty_overall_digest(self) -> Dict[str, Any]:
        """
        プレースホルダー付きoverall_digestを生成（Single Source of Truth）

        Returns:
            プレースホルダーを含むoverall_digest構造体
        """
        limits = PLACEHOLDER_LIMITS
        return {
            "timestamp": PLACEHOLDER_SIMPLE,
            "source_files": [],
            "digest_type": PLACEHOLDER_SIMPLE,
            "keywords": [
                f"{PLACEHOLDER_MARKER}: keyword{i}{PLACEHOLDER_END}"
                for i in range(1, limits["keyword_count"] + 1)
            ],
            "abstract": f"{PLACEHOLDER_MARKER}: 全体統合分析 ({limits['abstract_chars']}文字程度){PLACEHOLDER_END}",
            "impression": f"{PLACEHOLDER_MARKER}: 所感・展望 ({limits['impression_chars']}文字程度){PLACEHOLDER_END}"
        }

    def get_template(self) -> Dict[str, Any]:
        """
        ShadowGrandDigest.txtのテンプレートを返す

        Returns:
            ShadowGrandDigestの初期テンプレート構造
        """
        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": DIGEST_FORMAT_VERSION,
                "description": "GrandDigest更新後に作成された新しいコンテンツの増分ダイジェスト（下書き帳）"
            },
            "latest_digests": {
                level: {"overall_digest": self.create_empty_overall_digest()}
                for level in self.levels
            }
        }
