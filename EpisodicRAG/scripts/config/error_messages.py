#!/usr/bin/env python3
"""
Config層専用のエラーメッセージ関数
==================================

Config層をDomain層から独立させるためのシンプルなエラーメッセージ生成。
domain/error_formatter/config_errors.py の機能を簡略化して提供。

Usage:
    from config.error_messages import (
        invalid_level_message,
        config_key_missing_message,
        file_not_found_message,
        invalid_json_message,
    )
"""

from pathlib import Path
from typing import Any, List, Optional


def invalid_level_message(level: str, valid_levels: Optional[List[str]] = None) -> str:
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


def unknown_level_message(level: str) -> str:
    """
    不明なレベルエラーメッセージ

    Args:
        level: 指定された不明なレベル

    Returns:
        フォーマットされたエラーメッセージ
    """
    return f"Unknown level: '{level}'"


def config_key_missing_message(key: str) -> str:
    """
    設定キー欠落エラーメッセージ

    Args:
        key: 欠落している設定キー

    Returns:
        フォーマットされたエラーメッセージ
    """
    return f"Required configuration key missing: '{key}'"


def config_invalid_value_message(key: str, expected: str, actual: Any) -> str:
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


def config_section_missing_message(section: str) -> str:
    """
    設定セクション欠落エラーメッセージ

    Args:
        section: 欠落しているセクション名

    Returns:
        フォーマットされたエラーメッセージ
    """
    return f"'{section}' section missing in config.json"


def initialization_failed_message(component: str, error: Exception) -> str:
    """
    初期化失敗エラーメッセージ

    Args:
        component: 初期化に失敗したコンポーネント名
        error: 発生した例外

    Returns:
        フォーマットされたエラーメッセージ
    """
    return f"Failed to initialize {component}: {error}"


def file_not_found_message(path: Path) -> str:
    """
    ファイル未検出エラーメッセージ

    Args:
        path: 見つからなかったファイルのパス

    Returns:
        フォーマットされたエラーメッセージ
    """
    return f"File not found: {path}"


def invalid_json_message(path: Path, error: Exception) -> str:
    """
    無効なJSONエラーメッセージ

    Args:
        path: JSONファイルのパス
        error: パース時に発生した例外

    Returns:
        フォーマットされたエラーメッセージ
    """
    return f"Invalid JSON in {path}: {error}"


def directory_not_found_message(path: Path) -> str:
    """
    ディレクトリ未検出エラーメッセージ

    Args:
        path: 見つからなかったディレクトリのパス

    Returns:
        フォーマットされたエラーメッセージ
    """
    return f"Directory not found: {path}"
