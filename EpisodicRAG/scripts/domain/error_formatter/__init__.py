#!/usr/bin/env python3
"""
EpisodicRAG Error Formatter Package
===================================

エラーメッセージの標準化を担当するフォーマッタパッケージ。
カテゴリ別に分割されたフォーマッタを統合インターフェースで提供。

## 使用デザインパターン

### Singleton Pattern
get_error_formatter()でアクセスするSingletonインスタンス。
エラーフォーマッタはアプリケーション全体で共有されるため、
複数インスタンスを作成する意味がない。

テスト時はreset_error_formatter()でリセット可能。

### Composite Pattern
CompositeErrorFormatterクラスが複数のカテゴリ別フォーマッタを
統合し、単一のインターフェースで提供する。

呼び出し側は formatter.config.invalid_level() のように
カテゴリを明示的に指定してメソッドを呼び出す。

### Template Method Pattern (base.py)
BaseErrorFormatterクラスのformat_path()がテンプレートメソッド。
全サブクラスで共通のパス正規化ロジックを共有。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
- ConfigErrorFormatter: 設定関連エラーのみ
- FileErrorFormatter: ファイルI/Oエラーのみ
- ValidationErrorFormatter: バリデーションエラーのみ
- DigestErrorFormatter: ダイジェスト処理エラーのみ

### OCP (Open/Closed Principle)
新しいエラーカテゴリを追加する場合:
1. BaseErrorFormatterを継承した新クラスを作成
2. CompositeErrorFormatterに新属性として追加
既存コードの変更は最小限。

## テスト時の注意

テスト間でSingletonの状態が共有されるため、各テストの前後でリセットが必要。
pytest使用時はconftest.pyのreset_all_singletons() fixtureが自動的にリセットを行う。

手動リセット::

    from domain.error_formatter import reset_error_formatter
    reset_error_formatter()

Usage:
    from domain.error_formatter import get_error_formatter

    formatter = get_error_formatter()

    # カテゴリを明示的に指定
    msg = formatter.config.invalid_level("xyz", ["weekly", "monthly"])
    msg = formatter.file.file_not_found(path)
    msg = formatter.validation.invalid_type("field", "int", "hello")
    msg = formatter.digest.shadow_empty("weekly")
"""

from pathlib import Path
from typing import Optional

from domain.error_formatter.base import BaseErrorFormatter
from domain.error_formatter.config_errors import ConfigErrorFormatter
from domain.error_formatter.diagnostic import with_diagnostic_context
from domain.error_formatter.digest_errors import DigestErrorFormatter
from domain.error_formatter.file_errors import FileErrorFormatter
from domain.error_formatter.registry import FormatterRegistry
from domain.error_formatter.validation_errors import ValidationErrorFormatter

__all__ = [
    # クラス
    "BaseErrorFormatter",
    "ConfigErrorFormatter",
    "FileErrorFormatter",
    "ValidationErrorFormatter",
    "DigestErrorFormatter",
    "CompositeErrorFormatter",
    "FormatterRegistry",
    # 関数
    "get_error_formatter",
    "reset_error_formatter",
    "with_diagnostic_context",
]


class CompositeErrorFormatter:
    """
    全エラーフォーマッタを統合するComposite

    ## 使用デザインパターン
    - Composite: 複数のフォーマッタを1つのインターフェースで提供
    - Registry: 内部でFormatterRegistryを使用し、動的な拡張をサポート

    ## ARCHITECTURE: カテゴリベースアクセス
    formatter.config.invalid_level() のように、
    カテゴリを明示的に指定してメソッドを呼び出す。
    これにより:
    - どのカテゴリのエラーかが明確
    - IDE補完が効きやすい
    - 責務の分離が視覚的に明らか

    ## 拡張性
    register_formatter()メソッドで新しいカテゴリを動的に追加可能。

    Attributes:
        config: 設定関連エラーフォーマッタ
        file: ファイルI/O関連エラーフォーマッタ
        validation: バリデーション関連エラーフォーマッタ
        digest: ダイジェスト関連エラーフォーマッタ

    Example:
        formatter = CompositeErrorFormatter(project_root)
        formatter.config.invalid_level("xyz")
        formatter.file.file_not_found(path)

        # 動的に拡張
        formatter.register_formatter("custom", MyCustomFormatter(project_root))
        formatter.custom.my_error()
    """

    def __init__(self, project_root: Path) -> None:
        """
        初期化

        Args:
            project_root: プロジェクトルートパス（相対パス変換の基準）

        Example:
            >>> formatter = CompositeErrorFormatter(Path("/project"))
            >>> formatter.config.invalid_level("xyz")
            "Invalid level: 'xyz'"
        """
        self._project_root = project_root

        # ARCHITECTURE: FormatterRegistryを使用して内部管理
        self._registry = FormatterRegistry(project_root)

        # デフォルトフォーマッタを登録
        self._registry.register("config", ConfigErrorFormatter(project_root))
        self._registry.register("file", FileErrorFormatter(project_root))
        self._registry.register("validation", ValidationErrorFormatter(project_root))
        self._registry.register("digest", DigestErrorFormatter(project_root))

    @property
    def project_root(self) -> Path:
        """プロジェクトルートパス"""
        return self._project_root

    @property
    def registry(self) -> FormatterRegistry:
        """内部のFormatterRegistry（読み取り専用）"""
        return self._registry

    # =========================================================================
    # 後方互換性のためのプロパティ（既存コードはそのまま動作）
    # =========================================================================

    @property
    def config(self) -> ConfigErrorFormatter:
        """設定関連エラーフォーマッタ"""
        return self._registry.get("config")  # type: ignore[return-value]

    @property
    def file(self) -> FileErrorFormatter:
        """ファイルI/O関連エラーフォーマッタ"""
        return self._registry.get("file")  # type: ignore[return-value]

    @property
    def validation(self) -> ValidationErrorFormatter:
        """バリデーション関連エラーフォーマッタ"""
        return self._registry.get("validation")  # type: ignore[return-value]

    @property
    def digest(self) -> DigestErrorFormatter:
        """ダイジェスト関連エラーフォーマッタ"""
        return self._registry.get("digest")  # type: ignore[return-value]

    # =========================================================================
    # 拡張メソッド
    # =========================================================================

    def register_formatter(self, category: str, formatter: BaseErrorFormatter) -> None:
        """
        新しいカテゴリのフォーマッタを登録

        Args:
            category: カテゴリ名
            formatter: BaseErrorFormatterを継承したフォーマッタ

        Example:
            formatter.register_formatter("custom", MyCustomFormatter(project_root))
        """
        self._registry.register(category, formatter)

    def get_formatter(self, category: str) -> BaseErrorFormatter:
        """
        カテゴリ名でフォーマッタを取得

        Args:
            category: カテゴリ名

        Returns:
            登録済みフォーマッタ

        Raises:
            KeyError: カテゴリが未登録の場合

        Example:
            >>> formatter.get_formatter("config").invalid_level("xyz")
            "Invalid level: 'xyz'"
        """
        return self._registry.get(category)

    def has_formatter(self, category: str) -> bool:
        """
        カテゴリが登録済みか確認

        Args:
            category: カテゴリ名

        Returns:
            登録済みならTrue

        Example:
            >>> formatter.has_formatter("config")
            True
        """
        return self._registry.has(category)

    def format_path(self, path: Path) -> str:
        """
        パスを相対パスに正規化（便利メソッド）

        Args:
            path: 変換するパス

        Returns:
            相対パス文字列

        Example:
            >>> formatter.format_path(Path("/project/data/file.json"))
            'data/file.json'
        """
        # どのサブフォーマッタでも同じ結果なので、configを使用
        return self.config.format_path(path)


# =============================================================================
# Singleton アクセサ
# =============================================================================

_default_formatter: Optional[CompositeErrorFormatter] = None


def get_error_formatter(project_root: Optional[Path] = None) -> CompositeErrorFormatter:
    """
    CompositeErrorFormatterのインスタンスを取得

    ## ARCHITECTURE: Singleton with optional override
    - project_root省略時: キャッシュされたインスタンスを返す
    - project_root指定時: 新しいインスタンスを生成してキャッシュ

    Args:
        project_root: プロジェクトルート（省略時はカレントディレクトリ）

    Returns:
        CompositeErrorFormatterインスタンス

    Example:
        >>> formatter = get_error_formatter()
        >>> formatter.config.invalid_level("xyz")
        "Invalid level: 'xyz'"
    """
    global _default_formatter
    if _default_formatter is None or project_root is not None:
        root = project_root if project_root else Path.cwd()
        _default_formatter = CompositeErrorFormatter(root)
    return _default_formatter


def reset_error_formatter() -> None:
    """
    デフォルトフォーマッターをリセット（テスト用）

    Example:
        >>> reset_error_formatter()  # キャッシュをクリア
        >>> formatter = get_error_formatter()  # 新しいインスタンスが作成される
    """
    global _default_formatter
    _default_formatter = None
