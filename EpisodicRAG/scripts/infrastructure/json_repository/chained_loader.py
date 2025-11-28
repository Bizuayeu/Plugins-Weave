#!/usr/bin/env python3
"""
ChainedLoader - 戦略チェーン実行
================================

複数のLoadStrategyを順番に試行し、最初に成功したものを返す。

## 設計意図

ARCHITECTURE: Chain of Responsibility Pattern (GoF)
読み込み戦略を順番に試行するロジックを専用クラスに分離。
戦略の追加・削除・順序変更が容易になる。

## 使用例

```python
loader = ChainedLoader([
    FileLoadStrategy(safe_read_json),
    TemplateLoadStrategy(safe_read_json, save_json),
    FactoryLoadStrategy(save_json),
    DefaultLoadStrategy(),
])
result = loader.load(context)
```
"""

import logging
from typing import Any, Generic, List, Mapping, Optional, TypeVar

from infrastructure.json_repository.load_strategy import LoadContext, LoadStrategy

# モジュールロガー
logger = logging.getLogger("episodic_rag")

# Generic type for typed dict support
T = TypeVar("T", bound=Mapping[str, Any])


class ChainedLoader(Generic[T]):
    """
    戦略チェーンを実行するローダー

    ARCHITECTURE: Chain of Responsibility Pattern
    - 各戦略を順番に試行
    - 最初に成功した戦略の結果を返す
    - すべて失敗した場合はNoneを返す

    ARCHITECTURE: Open/Closed Principle (SOLID-O)
    - 新しい戦略を追加しても既存コードを変更不要
    - 戦略の順序を変えることで挙動をカスタマイズ可能
    """

    def __init__(self, strategies: List[LoadStrategy[T]]) -> None:
        """
        Args:
            strategies: 試行する戦略のリスト（順番に試行される）
        """
        self._strategies = strategies

    def load(self, context: LoadContext) -> Optional[T]:
        """
        戦略チェーンを実行

        Args:
            context: 読み込みコンテキスト

        Returns:
            最初に成功した戦略の結果、またはすべて失敗した場合はNone
        """
        logger.debug(
            f"ChainedLoader: Starting load for {context.target_file}, "
            f"template={context.template_file}"
        )

        for strategy in self._strategies:
            logger.debug(f"Trying: {strategy.get_description()}")
            result = strategy.load(context)
            if result is not None:
                logger.debug(f"Success: {strategy.get_description()}")
                return result

        logger.debug("ChainedLoader: All strategies exhausted, returning None")
        return None

    def add_strategy(self, strategy: LoadStrategy[T]) -> None:
        """
        戦略を追加

        Args:
            strategy: 追加する戦略（リストの最後に追加）
        """
        self._strategies.append(strategy)

    def insert_strategy(self, index: int, strategy: LoadStrategy[T]) -> None:
        """
        指定位置に戦略を挿入

        Args:
            index: 挿入位置
            strategy: 挿入する戦略
        """
        self._strategies.insert(index, strategy)


__all__ = ["ChainedLoader"]
