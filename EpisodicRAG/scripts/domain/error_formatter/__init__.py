#!/usr/bin/env python3
"""
EpisodicRAG Error Formatter Package
===================================

エラーメッセージの標準化を担当するフォーマッタパッケージ。
カテゴリ別に分割されたフォーマッタを統合インターフェースで提供。

## 使用デザインパターン

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
from domain.error_formatter.validation_errors import ValidationErrorFormatter

__all__ = [
    # クラス
    "BaseErrorFormatter",
    "ConfigErrorFormatter",
    "FileErrorFormatter",
    "ValidationErrorFormatter",
    "DigestErrorFormatter",
    "CompositeErrorFormatter",
    # 関数
    "get_error_formatter",
    "reset_error_formatter",
    "with_diagnostic_context",
]


class CompositeErrorFormatter:
    """
    全エラーフォーマッタを統合するComposite

    ## 使用デザインパターン
    Composite: 複数のフォーマッタを1つのインターフェースで提供

    ## ARCHITECTURE: カテゴリベースアクセス
    formatter.config.invalid_level() のように、
    カテゴリを明示的に指定してメソッドを呼び出す。
    これにより:
    - どのカテゴリのエラーかが明確
    - IDE補完が効きやすい
    - 責務の分離が視覚的に明らか

    Attributes:
        config: 設定関連エラーフォーマッタ
        file: ファイルI/O関連エラーフォーマッタ
        validation: バリデーション関連エラーフォーマッタ
        digest: ダイジェスト関連エラーフォーマッタ

    Example:
        formatter = CompositeErrorFormatter(project_root)
        formatter.config.invalid_level("xyz")
        formatter.file.file_not_found(path)
    """

    def __init__(self, project_root: Path) -> None:
        """
        初期化

        Args:
            project_root: プロジェクトルートパス（相対パス変換の基準）
        """
        self._project_root = project_root

        # ARCHITECTURE: 各カテゴリフォーマッタを属性として公開
        self.config = ConfigErrorFormatter(project_root)
        self.file = FileErrorFormatter(project_root)
        self.validation = ValidationErrorFormatter(project_root)
        self.digest = DigestErrorFormatter(project_root)

    @property
    def project_root(self) -> Path:
        """プロジェクトルートパス"""
        return self._project_root

    def format_path(self, path: Path) -> str:
        """
        パスを相対パスに正規化（便利メソッド）

        Args:
            path: 変換するパス

        Returns:
            相対パス文字列
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
    """
    global _default_formatter
    if _default_formatter is None or project_root is not None:
        root = project_root if project_root else Path.cwd()
        _default_formatter = CompositeErrorFormatter(root)
    return _default_formatter


def reset_error_formatter() -> None:
    """
    デフォルトフォーマッターをリセット（テスト用）
    """
    global _default_formatter
    _default_formatter = None
