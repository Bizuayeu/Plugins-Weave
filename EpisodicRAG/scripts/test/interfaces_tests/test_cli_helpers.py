#!/usr/bin/env python3
"""
CLI Helpers テスト
==================

CLI共通ヘルパー関数のテスト。
"""

import json
import sys
import unittest
from io import StringIO
from unittest.mock import patch

import pytest


class TestOutputJson(unittest.TestCase):
    """output_json関数のテスト"""

    @pytest.mark.unit
    def test_output_json_prints_valid_json(self) -> None:
        """JSONとして有効な出力を生成"""
        from interfaces.cli_helpers import output_json

        data = {"status": "ok", "message": "test"}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output_json(data)
            output = mock_stdout.getvalue()

        parsed = json.loads(output)
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["message"], "test")

    @pytest.mark.unit
    def test_output_json_uses_indent(self) -> None:
        """インデント付きで出力"""
        from interfaces.cli_helpers import output_json

        data = {"key": "value"}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output_json(data)
            output = mock_stdout.getvalue()

        # インデントがあれば改行が含まれる
        self.assertIn("\n", output)

    @pytest.mark.unit
    def test_output_json_preserves_unicode(self) -> None:
        """日本語などのUnicodeを保持"""
        from interfaces.cli_helpers import output_json

        data = {"message": "テスト"}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output_json(data)
            output = mock_stdout.getvalue()

        self.assertIn("テスト", output)

    @pytest.mark.unit
    def test_output_json_handles_nested_data(self) -> None:
        """ネストしたデータを正しく出力"""
        from interfaces.cli_helpers import output_json

        data = {"level1": {"level2": {"level3": "value"}}}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            output_json(data)
            output = mock_stdout.getvalue()

        parsed = json.loads(output)
        self.assertEqual(parsed["level1"]["level2"]["level3"], "value")


class TestOutputError(unittest.TestCase):
    """output_error関数のテスト"""

    @pytest.mark.unit
    def test_output_error_includes_status_error(self) -> None:
        """status: errorを含む"""
        from interfaces.cli_helpers import output_error

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                output_error("Test error")

        output = mock_stdout.getvalue()
        parsed = json.loads(output)
        self.assertEqual(parsed["status"], "error")
        self.assertEqual(exc_info.value.code, 1)

    @pytest.mark.unit
    def test_output_error_includes_error_message(self) -> None:
        """エラーメッセージを含む"""
        from interfaces.cli_helpers import output_error

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                output_error("Something went wrong")

        output = mock_stdout.getvalue()
        parsed = json.loads(output)
        self.assertEqual(parsed["error"], "Something went wrong")

    @pytest.mark.unit
    def test_output_error_includes_details_when_provided(self) -> None:
        """詳細情報を含む"""
        from interfaces.cli_helpers import output_error

        details = {"action": "Run setup", "code": 42}

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                output_error("Error occurred", details=details)

        output = mock_stdout.getvalue()
        parsed = json.loads(output)
        self.assertEqual(parsed["details"]["action"], "Run setup")
        self.assertEqual(parsed["details"]["code"], 42)

    @pytest.mark.unit
    def test_output_error_without_details(self) -> None:
        """詳細なしでも動作"""
        from interfaces.cli_helpers import output_error

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                output_error("Simple error")

        output = mock_stdout.getvalue()
        parsed = json.loads(output)
        self.assertNotIn("details", parsed)

    @pytest.mark.unit
    def test_output_error_exits_with_code_1(self) -> None:
        """終了コード1で終了"""
        from interfaces.cli_helpers import output_error

        with patch("sys.stdout", new_callable=StringIO):
            with pytest.raises(SystemExit) as exc_info:
                output_error("Exit test")

        self.assertEqual(exc_info.value.code, 1)

    @pytest.mark.unit
    def test_output_error_preserves_unicode(self) -> None:
        """日本語エラーメッセージを保持"""
        from interfaces.cli_helpers import output_error

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit):
                output_error("エラーが発生しました")

        output = mock_stdout.getvalue()
        self.assertIn("エラーが発生しました", output)


if __name__ == "__main__":
    unittest.main()
