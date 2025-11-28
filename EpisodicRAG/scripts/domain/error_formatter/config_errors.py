#!/usr/bin/env python3
"""
設定関連エラーフォーマッタ
==========================

レベル設定、設定ファイル、設定値に関するエラーメッセージを生成。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
このクラスは「設定関連エラーのフォーマット」という単一責務のみを持つ。
ファイルI/Oエラーやバリデーションエラーは別クラスが担当。
"""

from pathlib import Path
from typing import Any, List, Optional

from domain.error_formatter.base import BaseErrorFormatter


class ConfigErrorFormatter(BaseErrorFormatter):
    """
    設定関連エラーのフォーマッタ

    レベル設定、設定キー、設定値に関するエラーメッセージを
    一貫したフォーマットで生成する。

    Example:
        formatter = ConfigErrorFormatter(project_root)
        msg = formatter.invalid_level("xyz", ["weekly", "monthly"])
        # -> "Invalid level: 'xyz'. Valid levels: weekly, monthly"
    """

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
        不明なレベルエラーメッセージ

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

    def config_section_missing(self, section: str) -> str:
        """
        設定セクション欠落エラーメッセージ

        Args:
            section: 欠落しているセクション名

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"'{section}' section missing in config.json"

    def initialization_failed(self, component: str, error: Exception) -> str:
        """
        初期化失敗エラーメッセージ

        Args:
            component: 初期化に失敗したコンポーネント名
            error: 発生した例外

        Returns:
            フォーマットされたエラーメッセージ
        """
        return f"Failed to initialize {component}: {error}"
