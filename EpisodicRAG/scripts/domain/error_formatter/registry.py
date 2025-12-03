#!/usr/bin/env python3
"""
FormatterRegistry - Registry Pattern for Error Formatters
==========================================================

エラーフォーマッタの動的登録と取得を管理するRegistry。

## 使用デザインパターン

### Registry Pattern
フォーマッタをカテゴリ名で登録・取得可能にする。
動的な拡張と一貫したアクセスを両立。

## SOLID原則の実践

### OCP (Open/Closed Principle)
- 新しいカテゴリ追加時にCompositeErrorFormatterの変更不要
- register()メソッドで拡張可能

### DIP (Dependency Inversion Principle)
- BaseErrorFormatterインターフェースに依存
- 具体的なフォーマッタクラスへの依存を減少

Usage:
    from domain.error_formatter.registry import FormatterRegistry
    from domain.error_formatter import ConfigErrorFormatter

    registry = FormatterRegistry(project_root)
    registry.register("config", ConfigErrorFormatter(project_root))

    # 取得方法
    formatter = registry.get("config")
    formatter = registry.config  # 動的属性アクセス
"""

from pathlib import Path
from typing import Dict, Optional

from domain.error_formatter.base import BaseErrorFormatter


class FormatterRegistry:
    """
    エラーフォーマッタのRegistry

    カテゴリ名でフォーマッタを登録・取得する。
    動的な属性アクセスもサポート。

    Attributes:
        project_root: プロジェクトルートパス

    Example:
        registry = FormatterRegistry(project_root)
        registry.register("config", ConfigErrorFormatter(project_root))

        # 取得
        formatter = registry.get("config")
        formatter = registry.config  # 同等
    """

    def __init__(self, project_root: Path) -> None:
        """
        初期化

        Args:
            project_root: プロジェクトルートパス
        """
        self._project_root = project_root
        self._formatters: Dict[str, BaseErrorFormatter] = {}

    @property
    def project_root(self) -> Path:
        """プロジェクトルートパス"""
        return self._project_root

    def register(self, category: str, formatter: BaseErrorFormatter) -> None:
        """
        フォーマッタを登録

        Args:
            category: カテゴリ名（例: "config", "file"）
            formatter: BaseErrorFormatterを継承したフォーマッタ

        Raises:
            TypeError: formatterがBaseErrorFormatterを継承していない場合
        """
        if not isinstance(formatter, BaseErrorFormatter):
            raise TypeError(
                f"Formatter must be a BaseErrorFormatter subclass, got {type(formatter).__name__}"
            )
        self._formatters[category] = formatter

    def get(self, category: str) -> BaseErrorFormatter:
        """
        フォーマッタを取得

        Args:
            category: カテゴリ名

        Returns:
            登録済みフォーマッタ

        Raises:
            KeyError: カテゴリが未登録の場合
        """
        if category not in self._formatters:
            raise KeyError(
                f"Formatter category '{category}' not registered. "
                f"Available: {', '.join(self._formatters.keys()) or '(none)'}"
            )
        return self._formatters[category]

    def get_or_none(self, category: str) -> Optional[BaseErrorFormatter]:
        """
        フォーマッタを取得（未登録時はNone）

        Args:
            category: カテゴリ名

        Returns:
            登録済みフォーマッタ、または None
        """
        return self._formatters.get(category)

    def has(self, category: str) -> bool:
        """
        カテゴリが登録済みか確認

        Args:
            category: カテゴリ名

        Returns:
            登録済みならTrue
        """
        return category in self._formatters

    def categories(self) -> list[str]:
        """
        登録済みカテゴリ一覧を取得

        Returns:
            カテゴリ名のリスト
        """
        return list(self._formatters.keys())

    def __getattr__(self, name: str) -> BaseErrorFormatter:
        """
        動的属性アクセス: registry.config など

        Args:
            name: カテゴリ名

        Returns:
            登録済みフォーマッタ

        Raises:
            AttributeError: カテゴリが未登録の場合
        """
        # _formatters自体へのアクセスは通常の属性アクセス
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        try:
            return self.get(name)
        except KeyError as e:
            raise AttributeError(
                f"'{type(self).__name__}' has no formatter category '{name}'. "
                f"Available: {', '.join(self._formatters.keys()) or '(none)'}"
            ) from e

    def __contains__(self, category: str) -> bool:
        """'in' 演算子サポート"""
        return self.has(category)

    def __len__(self) -> int:
        """登録済みフォーマッタ数"""
        return len(self._formatters)
