# tests/test_main.py
"""
main.py のテスト

例外処理とエントリーポイントのテスト。
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from domain.exceptions import EmailingEssayError, MailError, SchedulerError, ValidationError
from main import main


class TestMainExceptionHandling:
    """main()の例外処理テスト"""

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_emailingessay_error_returns_1(self, mock_parser, mock_dispatch):
        """EmailingEssayErrorで終了コード1を返す"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.side_effect = MailError("test error")

        result = main()

        assert result == 1

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_scheduler_error_returns_1(self, mock_parser, mock_dispatch):
        """SchedulerErrorで終了コード1を返す"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.side_effect = SchedulerError("scheduler failed")

        result = main()

        assert result == 1

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_validation_error_returns_1(self, mock_parser, mock_dispatch):
        """ValidationErrorで終了コード1を返す"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.side_effect = ValidationError("invalid input")

        result = main()

        assert result == 1

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_value_error_returns_1(self, mock_parser, mock_dispatch):
        """ValueErrorで終了コード1を返す"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.side_effect = ValueError("invalid argument")

        result = main()

        assert result == 1

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_file_not_found_error_returns_1(self, mock_parser, mock_dispatch):
        """FileNotFoundErrorで終了コード1を返す"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.side_effect = FileNotFoundError("file not found")

        result = main()

        assert result == 1

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_permission_error_returns_1(self, mock_parser, mock_dispatch):
        """PermissionErrorで終了コード1を返す"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.side_effect = PermissionError("permission denied")

        result = main()

        assert result == 1

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_unexpected_error_returns_1(self, mock_parser, mock_dispatch):
        """予期しない例外で終了コード1を返す"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.side_effect = RuntimeError("unexpected")

        result = main()

        assert result == 1


class TestMainDispatch:
    """main()のディスパッチテスト"""

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_dispatch_returns_minus_1_shows_help(self, mock_parser, mock_dispatch):
        """dispatch()が-1を返すとヘルプ表示して0を返す"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.return_value = -1

        result = main()

        assert result == 0
        mock_parser.return_value.print_help.assert_called_once()

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_dispatch_returns_0_success(self, mock_parser, mock_dispatch):
        """dispatch()が0を返すと成功"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.return_value = 0

        result = main()

        assert result == 0

    @patch('main.dispatch')
    @patch('main.create_parser')
    def test_dispatch_returns_1_error(self, mock_parser, mock_dispatch):
        """dispatch()が1を返すとエラー"""
        mock_parser.return_value.parse_args.return_value = Mock()
        mock_dispatch.return_value = 1

        result = main()

        assert result == 1
