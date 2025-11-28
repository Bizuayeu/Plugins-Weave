#!/usr/bin/env python3
"""
エラーフォーマッタ基底クラス
============================

全てのカテゴリ別フォーマッタに共通する機能を提供する基底クラス。

## 使用デザインパターン

### Template Method Pattern
format_path() メソッドがテンプレートメソッドとして機能。
全サブクラスでパス正規化のロジックを共有しつつ、
各サブクラスは独自のエラーメッセージ生成に集中できる。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
- この基底クラスは「パス正規化」という単一責務のみ
- エラーメッセージ生成はサブクラスに委譲

### OCP (Open/Closed Principle)
- 新しいエラーカテゴリはこのクラスを継承するだけ
- 基底クラスの変更なしに拡張可能

### LSP (Liskov Substitution Principle)
- 全サブクラスはBaseErrorFormatterとして扱える
- format_path()の契約を全サブクラスが満たす
"""

from pathlib import Path


class BaseErrorFormatter:
    """
    エラーフォーマッタの基底クラス

    全てのカテゴリ別フォーマッタはこのクラスを継承し、
    共通のパス正規化機能を利用する。

    Attributes:
        project_root: 相対パス変換の基準となるプロジェクトルート

    Example:
        class MyErrorFormatter(BaseErrorFormatter):
            def my_error(self, detail: str) -> str:
                return f"My error: {detail}"
    """

    def __init__(self, project_root: Path) -> None:
        """
        初期化

        Args:
            project_root: プロジェクトルートパス（相対パス変換の基準）
        """
        self.project_root = project_root

    def format_path(self, path: Path) -> str:
        """
        パスを相対パスに正規化（Template Method）

        project_root を基準とした相対パスに変換。
        project_root 外のパスは絶対パスのまま返す。

        ## ARCHITECTURE: Template Method Pattern
        このメソッドが全サブクラスで共有される「テンプレート」。
        サブクラスはこのメソッドを呼び出すだけで、
        一貫したパス表記を実現できる。

        Args:
            path: 変換するパス

        Returns:
            相対パス文字列（可能な場合）、または絶対パス文字列
        """
        try:
            return str(path.relative_to(self.project_root))
        except ValueError:
            # project_root外のパスは絶対パスのまま
            return str(path)
