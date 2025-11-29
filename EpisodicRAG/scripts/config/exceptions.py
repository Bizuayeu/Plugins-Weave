#!/usr/bin/env python3
"""
Config層専用の例外
==================

Config層をDomain層から独立させるための例外クラス。
シンプルな例外として実装し、DiagnosticContextは持たない。

Usage:
    from config.exceptions import ConfigError

    raise ConfigError("Invalid config.json format")
"""


class ConfigError(Exception):
    """
    設定関連エラー

    Config層専用の例外クラス。Domain層のConfigErrorとは独立。

    Examples:
        - config.json が見つからない
        - config.json のフォーマットが不正
        - 必須の設定キーが存在しない
        - 無効なレベルが指定された

    Note:
        Domain層のEpisodicRAGErrorを継承しないため、
        `except EpisodicRAGError` ではキャッチされない。
        これはConfig層の独立性を保つための意図的な設計。
    """

    def __init__(self, message: str) -> None:
        """
        初期化

        Args:
            message: エラーメッセージ
        """
        super().__init__(message)
