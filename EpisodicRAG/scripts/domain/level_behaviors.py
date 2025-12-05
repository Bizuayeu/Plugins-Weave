#!/usr/bin/env python3
"""
Level Behaviors - Strategy Pattern for Level-specific Behavior
===============================================================

レベル固有の振る舞いを定義するStrategy pattern実装。

## 使用デザインパターン

### Strategy Pattern
レベルごとに異なる振る舞い（フォーマット、カスケード判定）を
LevelBehaviorインターフェースで抽象化。具体的な実装は
StandardLevelBehavior, LoopLevelBehaviorなどで提供。

新しいレベルタイプを追加する際は、LevelBehaviorを継承した
新クラスを作成するだけで対応可能（既存コード変更不要）。

## SOLID原則の実践

### OCP (Open/Closed Principle)
- 新しい振る舞い: LevelBehaviorを継承してRegisterに登録
- 既存コードの修正は一切不要

### DIP (Dependency Inversion Principle)
- LevelBehavior抽象クラスに依存し、具象クラスには依存しない
- 呼び出し側はget_behavior()経由でBehaviorを取得

Usage:
    from domain.level_behaviors import StandardLevelBehavior, LoopLevelBehavior
    from domain.level_metadata import LevelMetadata

    metadata = LevelMetadata(...)
    behavior = StandardLevelBehavior(metadata)
    formatted = behavior.format_number(42)  # "W0042"

Architecture:
    - LevelBehavior: レベル固有の振る舞い（Strategy interface）
    - StandardLevelBehavior: 通常レベルの実装
    - LoopLevelBehavior: Loopファイル専用の実装
"""

from abc import ABC, abstractmethod

from domain.level_metadata import LevelMetadata


class LevelBehavior(ABC):
    """
    レベル固有の振る舞いを定義するStrategy interface

    新しい振る舞いが必要な場合、このクラスを継承して実装を追加。
    既存コードを修正せずに拡張可能（OCP準拠）。

    Design Pattern: Strategy
        振る舞いをカプセル化し、実行時に交換可能にする。

    Learning Point:
        新しいレベルタイプを追加する際は、このクラスを継承した
        新クラスを作成するだけで対応可能。既存コードの修正は不要（OCP）。

    ## ARCHITECTURE: Strategy Pattern の Context
    このクラスが Strategy の抽象インターフェースを定義。
    StandardLevelBehavior, LoopLevelBehavior が具象 Strategy。
    LevelRegistry が Context として Strategy を保持・切り替える。

    Example:
        >>> class CustomBehavior(LevelBehavior):
        ...     def format_number(self, n: int) -> str:
        ...         return f"CUSTOM{n:03d}"
        ...     def should_cascade(self) -> bool:
        ...         return False
    """

    @abstractmethod
    def format_number(self, number: int) -> str:
        """
        番号をレベル固有のフォーマットに変換

        Args:
            number: フォーマットする番号

        Returns:
            フォーマットされた文字列（例: "W0042", "L00186"）

        Example:
            >>> behavior = StandardLevelBehavior(weekly_metadata)
            >>> behavior.format_number(42)
            'W0042'
        """
        ...

    @abstractmethod
    def should_cascade(self) -> bool:
        """
        このレベルが次レベルへカスケードするかどうか

        Returns:
            True: 次レベルへカスケードする
            False: カスケードしない（最上位、または特殊レベル）

        Example:
            >>> behavior = StandardLevelBehavior(weekly_metadata)
            >>> behavior.should_cascade()
            True
        """
        ...


class StandardLevelBehavior(LevelBehavior):
    """
    通常ダイジェストレベルの振る舞い

    LEVEL_CONFIGで定義された標準的なダイジェストレベル用。

    Example:
        >>> from domain.level_metadata import LevelMetadata
        >>> metadata = LevelMetadata("weekly", "W", 4, "1_Weekly", "loops", "monthly")
        >>> behavior = StandardLevelBehavior(metadata)
        >>> behavior.format_number(42)
        'W0042'
    """

    def __init__(self, metadata: LevelMetadata):
        """
        Args:
            metadata: このレベルのメタデータ

        Example:
            >>> metadata = LevelMetadata("weekly", "W", 4, "1_Weekly", "loops", "monthly")
            >>> behavior = StandardLevelBehavior(metadata)
        """
        self.metadata = metadata

    def format_number(self, number: int) -> str:
        """
        プレフィックス + ゼロパディング番号

        Example:
            >>> behavior = StandardLevelBehavior(weekly_metadata)
            >>> behavior.format_number(42)
            'W0042'
        """
        return f"{self.metadata.prefix}{number:0{self.metadata.digits}d}"

    def should_cascade(self) -> bool:
        """
        次レベルが存在すればカスケードする

        Example:
            >>> behavior = StandardLevelBehavior(weekly_metadata)
            >>> behavior.should_cascade()  # next_level="monthly"
            True
        """
        return self.metadata.next_level is not None


class LoopLevelBehavior(LevelBehavior):
    """
    Loopファイル専用の振る舞い

    Loopファイルは特殊なフォーマット（L00001）を持ち、
    カスケードは行わない。

    Example:
        >>> behavior = LoopLevelBehavior()
        >>> behavior.format_number(186)
        'L00186'
    """

    def format_number(self, number: int) -> str:
        """
        L + 5桁ゼロパディング

        Example:
            >>> behavior = LoopLevelBehavior()
            >>> behavior.format_number(186)
            'L00186'
        """
        return f"L{number:05d}"

    def should_cascade(self) -> bool:
        """
        Loopはカスケードしない

        Example:
            >>> behavior = LoopLevelBehavior()
            >>> behavior.should_cascade()
            False
        """
        return False
