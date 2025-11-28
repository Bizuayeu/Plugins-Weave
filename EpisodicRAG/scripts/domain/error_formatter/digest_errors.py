#!/usr/bin/env python3
"""
ダイジェスト関連エラーフォーマッタ
==================================

ダイジェスト処理、Shadow管理、カスケード処理に関するエラーメッセージを生成。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
このクラスは「ダイジェスト処理エラーのフォーマット」という単一責務のみを持つ。
EpisodicRAG固有のドメインエラーを担当。
"""

from pathlib import Path

from domain.error_formatter.base import BaseErrorFormatter


class DigestErrorFormatter(BaseErrorFormatter):
    """
    ダイジェスト関連エラーのフォーマッタ

    ダイジェスト処理、Shadow管理、カスケード処理に関するエラーメッセージを
    一貫したフォーマットで生成する。

    Example:
        formatter = DigestErrorFormatter(project_root)
        msg = formatter.shadow_empty("weekly")
        # -> "Shadow digest for level 'weekly' has no source files"
    """

    def digest_not_found(self, level: str, identifier: str) -> str:
        """
        ダイジェスト未検出エラーメッセージ

        Args:
            level: ダイジェストレベル
            identifier: ダイジェスト識別子

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Digest not found: level='{level}', id='{identifier}'"

    def shadow_empty(self, level: str) -> str:
        """
        Shadow空エラーメッセージ

        Args:
            level: ダイジェストレベル

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Shadow digest for level '{level}' has no source files"

    def cascade_error(self, from_level: str, to_level: str, reason: str) -> str:
        """
        カスケードエラーメッセージ

        Args:
            from_level: カスケード元レベル
            to_level: カスケード先レベル
            reason: エラー理由

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Cascade failed from '{from_level}' to '{to_level}': {reason}"
