#!/usr/bin/env python3
"""
Domain Protocols
================

依存関係逆転のためのProtocol定義。
循環インポートを回避し、クリーンな依存関係を実現。

Usage:
    from domain.protocols import LevelRegistryProtocol, LevelBehaviorProtocol

    def process_level(registry: LevelRegistryProtocol) -> None:
        behavior = registry.get_behavior("weekly")
        formatted = behavior.format_number(42)
"""

from typing import Optional, Protocol


class LevelBehaviorProtocol(Protocol):
    """
    レベル固有の振る舞いを定義するProtocol

    LevelBehavior実装クラスが満たすべきインターフェース。
    """

    def format_number(self, number: int) -> str:
        """
        番号をレベル固有のフォーマットに変換

        Args:
            number: フォーマットする番号

        Returns:
            フォーマットされた文字列（例: "W0042", "L00186"）
        """
        ...

    def should_cascade(self) -> bool:
        """
        このレベルが次レベルへカスケードするかどうか

        Returns:
            True: 次レベルへカスケードする
            False: カスケードしない
        """
        ...


class LevelRegistryProtocol(Protocol):
    """
    レベルとその振る舞いを管理するRegistryのProtocol

    LevelRegistryが満たすべきインターフェース。
    file_naming.pyがこのProtocolに依存することで、
    level_registry.pyへの直接依存を回避。
    """

    def build_prefix_pattern(self) -> str:
        """
        全プレフィックスの正規表現パターンを生成

        Returns:
            正規表現パターン文字列（例: "MD|W|M|Q|A|T|D|C|L"）
        """
        ...

    def get_behavior(self, level: str) -> LevelBehaviorProtocol:
        """
        レベルの振る舞いを取得

        Args:
            level: レベル名

        Returns:
            LevelBehavior実装
        """
        ...

    def get_level_by_prefix(self, prefix: str) -> Optional[str]:
        """
        プレフィックスからレベル名を逆引き

        Args:
            prefix: ファイル名プレフィックス

        Returns:
            レベル名、または見つからない場合None
        """
        ...


__all__ = ["LevelBehaviorProtocol", "LevelRegistryProtocol"]
