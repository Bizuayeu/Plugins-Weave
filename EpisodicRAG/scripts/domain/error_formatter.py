#!/usr/bin/env python3
"""
EpisodicRAG Error Formatter
===========================

エラーメッセージの標準化を担当するクラス。
一貫したパス表記、コンテキスト情報、メッセージフォーマットを提供。

Usage:
    from domain.error_formatter import ErrorFormatter

    formatter = ErrorFormatter(project_root)
    msg = formatter.invalid_level("xyz", ["weekly", "monthly"])
    raise ConfigError(msg)
"""

from pathlib import Path
from typing import Any, List, Optional


class ErrorFormatter:
    """
    エラーメッセージの標準化を担当

    全てのエラーメッセージを一貫したフォーマットで生成し、
    デバッグを容易にする。

    Features:
        - パスの相対パス正規化
        - 一貫したメッセージテンプレート
        - コンテキスト情報の標準化

    Example:
        formatter = ErrorFormatter(Path("/project/root"))
        msg = formatter.file_not_found(Path("/project/root/data/file.txt"))
        # -> "File not found: data/file.txt"
    """

    def __init__(self, project_root: Path):
        """
        初期化

        Args:
            project_root: プロジェクトルートパス（相対パス変換の基準）
        """
        self.project_root = project_root

    def format_path(self, path: Path) -> str:
        """
        パスを相対パスに正規化

        project_root を基準とした相対パスに変換。
        project_root 外のパスは絶対パスのまま返す。

        Args:
            path: 変換するパス

        Returns:
            相対パス文字列（可能な場合）、または絶対パス文字列
        """
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            return str(path)

    # =========================================================================
    # Level/Config Errors
    # =========================================================================

    def invalid_level(self, level: str, valid_levels: Optional[List[str]] = None) -> str:
        """
        無効なレベルエラーメッセージ

        Args:
            level: 指定された無効なレベル
            valid_levels: 有効なレベルのリスト（省略時は表示しない）

        Returns:
            フォーマットされたエラーメッセージ
        """
        if valid_levels:
            return f"Invalid level: '{level}'. Valid levels: {', '.join(valid_levels)}"
        return f"Invalid level: '{level}'"

    def unknown_level(self, level: str) -> str:
        """
        不明なレベルエラーメッセージ（invalid_level のエイリアス）

        Args:
            level: 指定された不明なレベル

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Unknown level: '{level}'"

    def config_key_missing(self, key: str) -> str:
        """
        設定キー欠落エラーメッセージ

        Args:
            key: 欠落している設定キー

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Required configuration key missing: '{key}'"

    def config_invalid_value(self, key: str, expected: str, actual: Any) -> str:
        """
        設定値不正エラーメッセージ

        Args:
            key: 設定キー
            expected: 期待される値の説明
            actual: 実際の値

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Invalid configuration value for '{key}': expected {expected}, got {type(actual).__name__}"

    # =========================================================================
    # File I/O Errors
    # =========================================================================

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

    # =========================================================================
    # Validation Errors
    # =========================================================================

    def invalid_type(self, context: str, expected: str, actual: Any) -> str:
        """
        型不正エラーメッセージ

        Args:
            context: エラーが発生したコンテキスト（フィールド名など）
            expected: 期待される型名
            actual: 実際の値

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"{context}: expected {expected}, got {type(actual).__name__}"

    def validation_error(self, field: str, reason: str, value: Optional[Any] = None) -> str:
        """
        バリデーションエラーメッセージ

        Args:
            field: バリデーションに失敗したフィールド名
            reason: 失敗の理由
            value: 実際の値（省略可能）

        Returns:
            フォーマットされたエラーメッセージ
        """
        if value is not None:
            return f"Validation failed for '{field}': {reason} (got: {value})"
        return f"Validation failed for '{field}': {reason}"

    def empty_collection(self, context: str) -> str:
        """
        空コレクションエラーメッセージ

        Args:
            context: エラーが発生したコンテキスト

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"{context} cannot be empty"

    # =========================================================================
    # Digest-specific Errors
    # =========================================================================

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


# =============================================================================
# Module-level convenience functions
# =============================================================================

# デフォルトのフォーマッターインスタンス（遅延初期化）
_default_formatter: Optional[ErrorFormatter] = None


def get_error_formatter(project_root: Optional[Path] = None) -> ErrorFormatter:
    """
    ErrorFormatterのインスタンスを取得

    Args:
        project_root: プロジェクトルート（省略時はカレントディレクトリ）

    Returns:
        ErrorFormatterインスタンス
    """
    global _default_formatter
    if _default_formatter is None or project_root is not None:
        root = project_root if project_root else Path.cwd()
        _default_formatter = ErrorFormatter(root)
    return _default_formatter


def reset_error_formatter() -> None:
    """
    デフォルトフォーマッターをリセット（テスト用）
    """
    global _default_formatter
    _default_formatter = None
