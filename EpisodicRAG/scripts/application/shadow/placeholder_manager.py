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
from infrastructure import log_info


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
            log_info(f"Initialized placeholder for {total_files} file(s)")
        else:
            log_info(f"Preserved existing analysis (now {total_files} file(s) total)")
            log_info(f"Claude should re-analyze all {total_files} files to integrate new content")
