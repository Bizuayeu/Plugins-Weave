# tests/domain/test_code_generator.py
"""
SafeCodeGenerator のテスト（Stage 4: エスケープロジック集中化）
"""

import os
import sys

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestSafeCodeGenerator:
    """SafeCodeGenerator クラスのテスト"""

    def test_escape_shell_command_backslash(self):
        """バックスラッシュがエスケープされる"""
        from domain.code_generator import SafeCodeGenerator

        result = SafeCodeGenerator.escape_for_python_string(r"C:\path\to\file")
        assert result == r"C:\\path\\to\\file"

    def test_escape_shell_command_quotes(self):
        """ダブルクォートがエスケープされる"""
        from domain.code_generator import SafeCodeGenerator

        result = SafeCodeGenerator.escape_for_python_string('echo "hello"')
        assert result == 'echo \\"hello\\"'

    def test_escape_handles_mixed_characters(self):
        """バックスラッシュとクォートの混合"""
        from domain.code_generator import SafeCodeGenerator

        result = SafeCodeGenerator.escape_for_python_string(r'C:\Users\test "quoted"')
        assert result == r'C:\\Users\\test \"quoted\"'

    def test_escape_empty_string(self):
        """空文字列"""
        from domain.code_generator import SafeCodeGenerator

        result = SafeCodeGenerator.escape_for_python_string("")
        assert result == ""

    def test_escape_no_special_characters(self):
        """特殊文字なし"""
        from domain.code_generator import SafeCodeGenerator

        result = SafeCodeGenerator.escape_for_python_string("simple command")
        assert result == "simple command"

    def test_escape_windows_path(self):
        """Windowsパスのエスケープ"""
        from domain.code_generator import SafeCodeGenerator

        result = SafeCodeGenerator.escape_for_python_string(
            r'python "C:\Users\anyth\scripts\main.py"'
        )
        expected = r'python \"C:\\Users\\anyth\\scripts\\main.py\"'
        assert result == expected

    def test_escape_multiple_backslashes(self):
        """連続バックスラッシュ"""
        from domain.code_generator import SafeCodeGenerator

        result = SafeCodeGenerator.escape_for_python_string(r"\\server\share")
        assert result == r"\\\\server\\share"
