# usecases/command_builder.py
"""
Claudeコマンド構築ユーティリティ

wait_essay と schedule_essay で使用されていた類似のコマンド構築ロジックを統合。
プラットフォーム依存のクォート処理を一元化し、保守性を向上。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal


QuoteStyle = Literal["single", "escaped", "auto"]


class ClaudeCommandBuilder:
    """Claudeコマンド引数の統一的な構築"""

    @staticmethod
    def get_quote_char(style: QuoteStyle = "auto") -> str:
        """
        クォート文字を取得する。

        Args:
            style: クォートスタイル
                - "single": シングルクォート（'）
                - "escaped": エスケープされたダブルクォート（\\"）
                - "auto": プラットフォームに応じて自動選択

        Returns:
            クォート文字
        """
        if style == "single":
            return "'"
        if style == "escaped":
            return '\\"'
        # auto: プラットフォーム依存
        return '\\"' if sys.platform == "win32" else "'"

    @staticmethod
    def normalize_path(path: str) -> str:
        """
        パスを正規化する（バックスラッシュをスラッシュに変換）。

        Args:
            path: ファイルパス

        Returns:
            正規化されたパス
        """
        return path.replace("\\", "/")

    @staticmethod
    def escape_for_quote(text: str, quote_char: str) -> str:
        """
        クォート文字に応じてテキストをエスケープする。

        Args:
            text: エスケープ対象のテキスト
            quote_char: 使用するクォート文字

        Returns:
            エスケープされたテキスト
        """
        if quote_char == "'":
            return text.replace("'", "\\'")
        if quote_char == '\\"':
            return text.replace('"', '\\"')
        return text

    @classmethod
    def build_args(
        cls,
        theme: str = "",
        context: str = "",
        file_list: str = "",
        lang: str = "",
        quote_style: QuoteStyle = "auto"
    ) -> str:
        """
        Claudeコマンドの引数部分を構築する。

        Args:
            theme: エッセイのテーマ
            context: コンテキストファイルパス
            file_list: ファイルリストパス
            lang: 言語（ja, en, auto）
            quote_style: クォートスタイル

        Returns:
            構築された引数文字列（例: "'theme' -c 'path' -l ja"）
        """
        q = cls.get_quote_char(quote_style)
        args: list[str] = []

        if theme:
            escaped_theme = cls.escape_for_quote(theme, q)
            args.append(f"{q}{escaped_theme}{q}")

        if context:
            safe_context = cls.normalize_path(context)
            args.append(f"-c {q}{safe_context}{q}")

        if file_list:
            safe_file_list = cls.normalize_path(file_list)
            args.append(f"-f {q}{safe_file_list}{q}")

        if lang:
            args.append(f"-l {lang}")

        return " ".join(args)

    @classmethod
    def build_full_command(
        cls,
        theme: str = "",
        context: str = "",
        file_list: str = "",
        lang: str = ""
    ) -> str:
        """
        完全なClaudeコマンドを構築する（OSスケジューラ用）。

        Args:
            theme: エッセイのテーマ
            context: コンテキストファイルパス
            file_list: ファイルリストパス
            lang: 言語

        Returns:
            完全なコマンド文字列（例: "claude --dangerously-skip-permissions -p '/essay ...'"）
        """
        # スケジューラ用は常にescapedスタイル（schtasksコマンド経由のため）
        args_str = cls.build_args(
            theme=theme,
            context=context,
            file_list=file_list,
            lang=lang,
            quote_style="escaped" if sys.platform == "win32" else "single"
        )

        if sys.platform == "win32":
            claude_path = str(Path.home() / ".local" / "bin" / "claude.exe")
            return f'"{claude_path}" --dangerously-skip-permissions -p "/essay {args_str}"'
        return f'claude --dangerously-skip-permissions -p "/essay {args_str}"'


# 後方互換性のための便利関数
def build_claude_args(
    theme: str = "",
    context: str = "",
    file_list: str = "",
    lang: str = "",
    quote_style: QuoteStyle = "single"
) -> str:
    """
    Claudeコマンド引数を構築する（後方互換性用）。

    wait_essay用のデフォルト: シングルクォート
    """
    return ClaudeCommandBuilder.build_args(
        theme=theme,
        context=context,
        file_list=file_list,
        lang=lang,
        quote_style=quote_style
    )


def build_claude_command(
    theme: str = "",
    context: str = "",
    file_list: str = "",
    lang: str = ""
) -> str:
    """
    完全なClaudeコマンドを構築する（後方互換性用）。

    schedule_essay用
    """
    return ClaudeCommandBuilder.build_full_command(
        theme=theme,
        context=context,
        file_list=file_list,
        lang=lang
    )
