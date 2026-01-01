# domain/code_generator.py
"""
安全なコード生成ユーティリティ

Stage 4: SafeCodeGenerator - エスケープロジックの集中化
コード生成時のエスケープ処理を一元化し、セキュリティ監査を容易にする。
"""

from __future__ import annotations


class SafeCodeGenerator:
    """
    安全なコード生成のためのユーティリティクラス

    Pythonコード内に埋め込む文字列のエスケープ処理を提供する。
    """

    @staticmethod
    def escape_for_python_string(value: str) -> str:
        """
        Python文字列リテラル内で使用するためにエスケープする。

        ダブルクォートで囲まれた文字列内で安全に使用できるようにする。

        Args:
            value: エスケープする文字列

        Returns:
            エスケープされた文字列

        Examples:
            >>> SafeCodeGenerator.escape_for_python_string(r'C:\\path\\to\\file')
            'C:\\\\path\\\\to\\\\file'
            >>> SafeCodeGenerator.escape_for_python_string('echo "hello"')
            'echo \\"hello\\"'
        """
        # バックスラッシュを先にエスケープ（順序重要）
        result = value.replace("\\", "\\\\")
        # ダブルクォートをエスケープ
        result = result.replace('"', '\\"')
        return result


__all__ = ["SafeCodeGenerator"]
