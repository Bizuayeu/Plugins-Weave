#!/usr/bin/env python3
"""
Placeholder Manager
===================

PLACEHOLDER管理（更新・保持判定）
"""

from domain.constants import (
    PLACEHOLDER_LIMITS,
    PLACEHOLDER_MARKER,
    create_placeholder_keywords,
    create_placeholder_text,
)
from domain.types import OverallDigestData
from infrastructure import get_structured_logger

_logger = get_structured_logger(__name__)


class PlaceholderManager:
    """PLACEHOLDERの管理クラス"""

    def update_or_preserve(self, overall_digest: OverallDigestData, total_files: int) -> None:
        """
        PLACEHOLDERの更新または既存分析の保持

        Args:
            overall_digest: overall_digestデータ
            total_files: 総ファイル数
        """
        abstract = overall_digest.get("abstract", "")
        is_placeholder = not abstract or (
            isinstance(abstract, str) and PLACEHOLDER_MARKER in abstract
        )

        if is_placeholder:
            limits = PLACEHOLDER_LIMITS
            overall_digest["abstract"] = create_placeholder_text(
                f"{total_files}ファイル分の全体統合分析", limits['abstract_chars']
            )
            overall_digest["impression"] = create_placeholder_text(
                "所感・展望", limits['impression_chars']
            )
            overall_digest["keywords"] = create_placeholder_keywords(limits["keyword_count"])
            _logger.info(f"プレースホルダー初期化: {total_files}ファイル")
        else:
            _logger.info(f"既存分析を保持（現在 {total_files}ファイル）")
            _logger.info(f"Claudeによる全{total_files}ファイルの再分析が必要（新規コンテンツ統合）")
