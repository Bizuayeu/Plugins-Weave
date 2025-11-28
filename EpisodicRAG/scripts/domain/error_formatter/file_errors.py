#!/usr/bin/env python3
"""
ファイルI/O関連エラーフォーマッタ
=================================

ファイル読み書き、ディレクトリ操作、JSON解析に関するエラーメッセージを生成。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
このクラスは「ファイルI/Oエラーのフォーマット」という単一責務のみを持つ。
設定エラーやダイジェストエラーは別クラスが担当。
"""

from pathlib import Path

from domain.error_formatter.base import BaseErrorFormatter


class FileErrorFormatter(BaseErrorFormatter):
    """
    ファイルI/O関連エラーのフォーマッタ

    ファイル操作、ディレクトリ操作、JSON解析に関するエラーメッセージを
    一貫したフォーマットで生成する。

    全てのパスは format_path() により相対パスに正規化される。

    Example:
        formatter = FileErrorFormatter(project_root)
        msg = formatter.file_not_found(Path("/project/data/missing.json"))
        # -> "File not found: data/missing.json"
    """

    def file_not_found(self, path: Path) -> str:
        """
        ファイル未検出エラーメッセージ

        Args:
            path: 見つからなかったファイルパス

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"File not found: {self.format_path(path)}"

    def file_already_exists(self, path: Path) -> str:
        """
        ファイル既存エラーメッセージ

        Args:
            path: 既に存在するファイルパス

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"File already exists: {self.format_path(path)}"

    def file_io_error(self, operation: str, path: Path, error: Exception) -> str:
        """
        ファイルI/Oエラーメッセージ

        Args:
            operation: 実行しようとした操作（"read", "write", "delete" など）
            path: 対象ファイルパス
            error: 発生した例外

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Failed to {operation} {self.format_path(path)}: {error}"

    def directory_not_found(self, path: Path) -> str:
        """
        ディレクトリ未検出エラーメッセージ

        Args:
            path: 見つからなかったディレクトリパス

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Directory not found: {self.format_path(path)}"

    def directory_creation_failed(self, path: Path, error: Exception) -> str:
        """
        ディレクトリ作成失敗エラーメッセージ

        Args:
            path: 作成に失敗したディレクトリパス
            error: 発生した例外

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Failed to create directory {self.format_path(path)}: {error}"

    def invalid_json(self, path: Path, error: Exception) -> str:
        """
        JSON不正エラーメッセージ

        Args:
            path: 不正なJSONファイルパス
            error: 発生した例外

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Invalid JSON in {self.format_path(path)}: {error}"
