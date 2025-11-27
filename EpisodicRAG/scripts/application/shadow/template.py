#!/usr/bin/env python3
"""
Shadow Template Generator
=========================

ShadowGrandDigestのテンプレートとプレースホルダー生成を担当
"""

from datetime import datetime
from typing import List

from domain.constants import (
    PLACEHOLDER_LIMITS,
    PLACEHOLDER_SIMPLE,
    create_placeholder_keywords,
    create_placeholder_text,
)
from domain.types import OverallDigestData, ShadowDigestData
from domain.version import DIGEST_FORMAT_VERSION


class ShadowTemplate:
    """ShadowGrandDigestテンプレート生成クラス"""

    def __init__(self, levels: List[str]):
        """
        初期化

        Args:
            levels: レベル名のリスト（例: ["weekly", "monthly", ...]）
        """
        self.levels = levels

    def create_empty_overall_digest(self) -> OverallDigestData:
        """
        プレースホルダー付きoverall_digestを生成（Single Source of Truth）

        Returns:
            プレースホルダーを含むoverall_digest構造体

        Note:
            戻り値の型はOverallDigestDataですが、実際にはプレースホルダー文字列が含まれます。
            Claudeによる分析後に正しい値に置き換えられます。
        """
        limits = PLACEHOLDER_LIMITS
        return {
            "timestamp": PLACEHOLDER_SIMPLE,
            "source_files": [],
            "digest_type": PLACEHOLDER_SIMPLE,
            "keywords": create_placeholder_keywords(limits["keyword_count"]),
            "abstract": create_placeholder_text("全体統合分析", limits['abstract_chars']),
            "impression": create_placeholder_text("所感・展望", limits['impression_chars']),
        }

    def get_template(self) -> ShadowDigestData:
        """
        ShadowGrandDigest.txtのテンプレートを返す

        Returns:
            ShadowGrandDigestの初期テンプレート構造
        """
        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": DIGEST_FORMAT_VERSION,
                "description": "GrandDigest更新後に作成された新しいコンテンツの増分ダイジェスト（下書き帳）",
            },
            "latest_digests": {
                level: {"overall_digest": self.create_empty_overall_digest()}
                for level in self.levels
            },
        }
