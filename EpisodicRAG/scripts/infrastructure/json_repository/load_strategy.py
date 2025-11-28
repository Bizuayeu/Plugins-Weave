#!/usr/bin/env python3
"""
LoadStrategy - JSON読み込み戦略
================================

Strategy Patternを使用したJSON読み込みの抽象化。

## 設計意図

ARCHITECTURE: Strategy Pattern適用
load_json_with_templateの3段階フォールバックロジックを
個別の戦略クラスに分離し、テスト容易性と拡張性を向上。

## 戦略クラス一覧

| クラス | 役割 |
|--------|------|
| LoadStrategy | 抽象基底クラス（ABC） |
| FileLoadStrategy | 既存ファイルからの読み込み |
| TemplateLoadStrategy | テンプレートファイルからの読み込み |
| FactoryLoadStrategy | ファクトリ関数からの生成 |
| DefaultLoadStrategy | 空dictのフォールバック |

## Chain of Responsibility

ChainedLoaderが戦略を順番に試行し、最初に成功したものを返す。
これにより、フォールバックロジックが宣言的に表現される。
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, Generic, Mapping, Optional, TypeVar, cast

# モジュールロガー
logger = logging.getLogger("episodic_rag")

# Generic type for typed dict support
T = TypeVar("T", bound=Mapping[str, Any])


class LoadStrategy(ABC, Generic[T]):
    """
    JSON読み込み戦略の抽象基底クラス

    ARCHITECTURE: Strategy Pattern（GoF）
    - 各具象クラスが異なる読み込みアルゴリズムをカプセル化
    - ChainedLoaderがコンテキストとして戦略を切り替える
    """

    @abstractmethod
    def load(self, context: "LoadContext") -> Optional[T]:
        """
        JSON読み込みを試行

        Args:
            context: 読み込みに必要な情報を持つコンテキスト

        Returns:
            読み込んだdict、または読み込み不可の場合はNone
        """
        ...

    @abstractmethod
    def get_description(self) -> str:
        """戦略の説明（デバッグ/ログ用）"""
        ...


class LoadContext:
    """
    読み込みコンテキスト - 各戦略に渡す情報をカプセル化

    ARCHITECTURE: Context Object Pattern
    戦略が必要とする情報を1つのオブジェクトにまとめることで、
    戦略のインターフェースをシンプルに保つ。
    """

    def __init__(
        self,
        target_file: Path,
        template_file: Optional[Path] = None,
        default_factory: Optional[Callable[[], Any]] = None,
        save_on_create: bool = True,
        log_message: Optional[str] = None,
    ) -> None:
        """
        Args:
            target_file: 読み込むJSONファイルのパス
            template_file: テンプレートファイルのパス（オプション）
            default_factory: デフォルト値を生成する関数（オプション）
            save_on_create: 作成時に保存するかどうか
            log_message: 作成時のログメッセージ
        """
        self.target_file = target_file
        self.template_file = template_file
        self.default_factory = default_factory
        self.save_on_create = save_on_create
        self.log_message = log_message


class FileLoadStrategy(LoadStrategy[T]):
    """
    既存ファイルからの読み込み戦略

    最優先で試行される。ファイルが存在すればその内容を返す。
    """

    def __init__(self, read_func: Callable[[Path, bool], Optional[Dict[str, Any]]]) -> None:
        """
        Args:
            read_func: JSON読み込み関数（_safe_read_json相当）
        """
        self._read_func = read_func

    def load(self, context: LoadContext) -> Optional[T]:
        """既存ファイルから読み込み"""
        if not context.target_file.exists():
            return None
        logger.debug(f"Loading existing file: {context.target_file}")
        raw_data = self._read_func(context.target_file, True)
        if raw_data:
            logger.debug(f"Loaded {len(raw_data)} keys from {context.target_file.name}")
        return cast(Optional[T], raw_data)

    def get_description(self) -> str:
        return "FileLoadStrategy: Load from existing file"


class TemplateLoadStrategy(LoadStrategy[T]):
    """
    テンプレートファイルからの読み込み戦略

    ターゲットファイルが存在しない場合にテンプレートから初期化。
    """

    def __init__(
        self,
        read_func: Callable[[Path, bool], Optional[Dict[str, Any]]],
        save_func: Callable[[Path, Dict[str, Any]], None],
    ) -> None:
        """
        Args:
            read_func: JSON読み込み関数
            save_func: JSON保存関数
        """
        self._read_func = read_func
        self._save_func = save_func

    def load(self, context: LoadContext) -> Optional[T]:
        """テンプレートから読み込み・保存"""
        if not context.template_file or not context.template_file.exists():
            return None

        logger.debug(f"Target not found, loading from template: {context.template_file}")
        raw_template = self._read_func(context.template_file, True)

        if raw_template is not None and context.save_on_create:
            self._save_func(context.target_file, raw_template)
            logger.debug(f"Saved initialized file to: {context.target_file}")

        if raw_template is not None:
            msg = context.log_message or f"Initialized {context.target_file.name} from template"
            logger.info(msg)

        return cast(Optional[T], raw_template)

    def get_description(self) -> str:
        return "TemplateLoadStrategy: Initialize from template file"


class FactoryLoadStrategy(LoadStrategy[T]):
    """
    ファクトリ関数からの生成戦略

    テンプレートも存在しない場合にファクトリ関数でデフォルト値を生成。
    """

    def __init__(self, save_func: Callable[[Path, Dict[str, Any]], None]) -> None:
        """
        Args:
            save_func: JSON保存関数
        """
        self._save_func = save_func

    def load(self, context: LoadContext) -> Optional[T]:
        """ファクトリから作成・保存"""
        if not context.default_factory:
            return None

        logger.debug("No template found, using default_factory")
        result: T = context.default_factory()

        if context.save_on_create:
            self._save_func(context.target_file, cast(Dict[str, Any], result))
            logger.debug(f"Saved default template to: {context.target_file}")

        msg = context.log_message or f"Created {context.target_file.name} with default template"
        logger.info(msg)
        return result

    def get_description(self) -> str:
        return "FactoryLoadStrategy: Create from default_factory"


class DefaultLoadStrategy(LoadStrategy[T]):
    """
    デフォルト値を返す最終フォールバック戦略

    他のすべての戦略が失敗した場合に空dictを返す。
    """

    def load(self, context: LoadContext) -> Optional[T]:
        """空dictを返す"""
        logger.debug("No template or factory provided, returning empty dict")
        return cast(T, {})

    def get_description(self) -> str:
        return "DefaultLoadStrategy: Return empty dict"


__all__ = [
    "LoadStrategy",
    "LoadContext",
    "FileLoadStrategy",
    "TemplateLoadStrategy",
    "FactoryLoadStrategy",
    "DefaultLoadStrategy",
]
