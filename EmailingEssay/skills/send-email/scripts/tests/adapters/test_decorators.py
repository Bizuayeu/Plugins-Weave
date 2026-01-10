# tests/adapters/test_decorators.py
"""
デコレータのテスト（Stage 2: バリデーション重複解消）
"""

import os
import sys
from argparse import Namespace
from unittest.mock import Mock, patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestValidateConfigDecorator:
    """@validate_config デコレータのテスト"""

    def test_decorator_passes_when_config_is_valid(self):
        """設定が有効な場合、ハンドラが実行される"""
        from adapters.cli.decorators import validate_config

        mock_handler = Mock(return_value=0)
        decorated = validate_config(mock_handler)

        with patch("adapters.cli.decorators.Config") as mock_config_cls:
            mock_config = Mock()
            mock_config.validate.return_value = []  # エラーなし
            mock_config_cls.load.return_value = mock_config

            args = Namespace(command="test")
            result = decorated(args)

        assert result == 0
        mock_handler.assert_called_once_with(args)

    def test_decorator_returns_1_when_config_is_invalid(self):
        """設定が無効な場合、ハンドラは実行されず1を返す"""
        from adapters.cli.decorators import validate_config

        mock_handler = Mock(return_value=0)
        decorated = validate_config(mock_handler)

        with patch("adapters.cli.decorators.Config") as mock_config_cls:
            mock_config = Mock()
            mock_config.validate.return_value = ["Missing SMTP config"]
            mock_config_cls.load.return_value = mock_config

            args = Namespace(command="test")
            result = decorated(args)

        assert result == 1
        mock_handler.assert_not_called()

    def test_decorator_prints_error_messages(self, capsys):
        """設定エラーがある場合、エラーメッセージを出力する"""
        from adapters.cli.decorators import validate_config

        mock_handler = Mock(return_value=0)
        decorated = validate_config(mock_handler)

        with patch("adapters.cli.decorators.Config") as mock_config_cls:
            mock_config = Mock()
            mock_config.validate.return_value = ["Error 1", "Error 2"]
            mock_config_cls.load.return_value = mock_config

            args = Namespace(command="test")
            decorated(args)

        captured = capsys.readouterr()
        assert "Error 1" in captured.out
        assert "Error 2" in captured.out

    def test_decorator_preserves_handler_return_value(self):
        """ハンドラの戻り値が保持される"""
        from adapters.cli.decorators import validate_config

        mock_handler = Mock(return_value=42)
        decorated = validate_config(mock_handler)

        with patch("adapters.cli.decorators.Config") as mock_config_cls:
            mock_config = Mock()
            mock_config.validate.return_value = []
            mock_config_cls.load.return_value = mock_config

            args = Namespace(command="test")
            result = decorated(args)

        assert result == 42

    def test_decorator_preserves_function_name(self):
        """デコレータがfunctools.wrapsを使用して関数名を保持する"""
        from adapters.cli.decorators import validate_config

        @validate_config
        def original_function(args: Namespace) -> int:
            """Original docstring"""
            return 0

        assert original_function.__name__ == "original_function"
        assert original_function.__doc__ == "Original docstring"
