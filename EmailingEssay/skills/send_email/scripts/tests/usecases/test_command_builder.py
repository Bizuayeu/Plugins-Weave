# tests/usecases/test_command_builder.py
"""
ClaudeCommandBuilderのテスト

command_builder.pyの全ブランチをカバーする。
"""

import sys

import pytest

from usecases.command_builder import (
    ClaudeCommandBuilder,
    build_claude_args,
    build_claude_command,
)


class TestGetQuoteChar:
    """get_quote_charメソッドのテスト"""

    def test_single_returns_single_quote(self):
        """style='single'はシングルクォートを返す"""
        result = ClaudeCommandBuilder.get_quote_char("single")
        assert result == "'"

    def test_escaped_returns_escaped_double_quote(self):
        """style='escaped'はエスケープされたダブルクォートを返す"""
        result = ClaudeCommandBuilder.get_quote_char("escaped")
        assert result == '\\"'

    def test_auto_returns_platform_specific(self, monkeypatch):
        """style='auto'はプラットフォームに応じた値を返す"""
        # Windows
        monkeypatch.setattr(sys, "platform", "win32")
        result = ClaudeCommandBuilder.get_quote_char("auto")
        assert result == '\\"'

        # Unix/Linux/Mac
        monkeypatch.setattr(sys, "platform", "linux")
        result = ClaudeCommandBuilder.get_quote_char("auto")
        assert result == "'"


class TestNormalizePath:
    """normalize_pathメソッドのテスト"""

    def test_converts_backslashes_to_forward_slashes(self):
        """バックスラッシュをスラッシュに変換"""
        result = ClaudeCommandBuilder.normalize_path("C:\\Users\\test\\file.txt")
        assert result == "C:/Users/test/file.txt"

    def test_preserves_forward_slashes(self):
        """スラッシュはそのまま"""
        result = ClaudeCommandBuilder.normalize_path("/home/user/file.txt")
        assert result == "/home/user/file.txt"

    def test_handles_mixed_slashes(self):
        """混在したスラッシュを処理"""
        result = ClaudeCommandBuilder.normalize_path("C:\\Users/test\\file.txt")
        assert result == "C:/Users/test/file.txt"


class TestEscapeForQuote:
    """escape_for_quoteメソッドのテスト"""

    def test_escapes_single_quotes_for_single_quote_char(self):
        """シングルクォート文字の場合はシングルクォートをエスケープ"""
        result = ClaudeCommandBuilder.escape_for_quote("it's a test", "'")
        assert result == "it\\'s a test"

    def test_escapes_double_quotes_for_escaped_quote_char(self):
        """エスケープダブルクォート文字の場合はダブルクォートをエスケープ"""
        result = ClaudeCommandBuilder.escape_for_quote('say "hello"', '\\"')
        assert result == 'say \\"hello\\"'

    def test_no_escape_for_other_quote_chars(self):
        """その他のクォート文字の場合はエスケープしない"""
        result = ClaudeCommandBuilder.escape_for_quote("test text", "other")
        assert result == "test text"


class TestBuildArgs:
    """build_argsメソッドのテスト"""

    def test_empty_args_returns_empty_string(self):
        """引数なしは空文字列"""
        result = ClaudeCommandBuilder.build_args()
        assert result == ""

    def test_theme_only(self):
        """テーマのみ"""
        result = ClaudeCommandBuilder.build_args(theme="テスト", quote_style="single")
        assert result == "'テスト'"

    def test_context_only(self):
        """コンテキストのみ"""
        result = ClaudeCommandBuilder.build_args(context="/path/to/context.md", quote_style="single")
        assert result == "-c '/path/to/context.md'"

    def test_file_list_only(self):
        """ファイルリストのみ"""
        result = ClaudeCommandBuilder.build_args(file_list="/path/to/files.txt", quote_style="single")
        assert result == "-f '/path/to/files.txt'"

    def test_lang_only(self):
        """言語のみ"""
        result = ClaudeCommandBuilder.build_args(lang="ja")
        assert result == "-l ja"

    def test_all_args_combined(self):
        """全引数の組み合わせ"""
        result = ClaudeCommandBuilder.build_args(
            theme="テスト",
            context="/path/to/context.md",
            file_list="/path/to/files.txt",
            lang="ja",
            quote_style="single",
        )
        assert "'テスト'" in result
        assert "-c '/path/to/context.md'" in result
        assert "-f '/path/to/files.txt'" in result
        assert "-l ja" in result

    def test_windows_path_normalization_in_context(self):
        """コンテキストパスのWindows形式正規化"""
        result = ClaudeCommandBuilder.build_args(
            context="C:\\Users\\test\\context.md",
            quote_style="single",
        )
        assert "-c 'C:/Users/test/context.md'" in result

    def test_windows_path_normalization_in_file_list(self):
        """ファイルリストパスのWindows形式正規化"""
        result = ClaudeCommandBuilder.build_args(
            file_list="C:\\Users\\test\\files.txt",
            quote_style="single",
        )
        assert "-f 'C:/Users/test/files.txt'" in result


class TestBuildFullCommand:
    """build_full_commandメソッドのテスト"""

    def test_windows_command(self, monkeypatch):
        """Windowsコマンド構築"""
        monkeypatch.setattr(sys, "platform", "win32")
        result = ClaudeCommandBuilder.build_full_command(theme="テスト")

        assert "claude.exe" in result
        assert "--dangerously-skip-permissions" in result
        assert '/essay \\"テスト\\"' in result

    def test_unix_command(self, monkeypatch):
        """Unix/Linux/Macコマンド構築"""
        monkeypatch.setattr(sys, "platform", "linux")
        result = ClaudeCommandBuilder.build_full_command(theme="テスト")

        assert result.startswith("claude --dangerously-skip-permissions")
        assert "'/essay 'テスト''" in result or "/essay 'テスト'" in result

    def test_unix_command_with_all_args(self, monkeypatch):
        """Unix/Linux/Macコマンド全引数"""
        monkeypatch.setattr(sys, "platform", "linux")
        result = ClaudeCommandBuilder.build_full_command(
            theme="週次振り返り",
            context="/home/user/context.md",
            file_list="/home/user/files.txt",
            lang="ja",
        )

        assert "claude --dangerously-skip-permissions" in result
        assert "週次振り返り" in result
        assert "-c '/home/user/context.md'" in result
        assert "-f '/home/user/files.txt'" in result
        assert "-l ja" in result


class TestBackwardCompatibilityFunctions:
    """後方互換性関数のテスト"""

    def test_build_claude_args_default_is_single_quote(self):
        """build_claude_argsのデフォルトはシングルクォート"""
        result = build_claude_args(theme="テスト")
        assert result == "'テスト'"

    def test_build_claude_args_with_escaped_style(self):
        """build_claude_argsでescapedスタイル指定"""
        result = build_claude_args(theme="テスト", quote_style="escaped")
        assert result == '\\"テスト\\"'

    def test_build_claude_command_delegates_correctly(self, monkeypatch):
        """build_claude_commandが正しく委譲する"""
        monkeypatch.setattr(sys, "platform", "win32")
        result = build_claude_command(theme="テスト")

        assert "claude.exe" in result
        assert "--dangerously-skip-permissions" in result
