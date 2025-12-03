#!/usr/bin/env python3
"""
test_cli.py
===========

config/cli.py のユニットテスト。
CLIエントリーポイントの動作を検証。
"""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCliMain:
    """config.cli.main() 関数のテスト"""

    @pytest.mark.integration
    def test_main_no_arguments_outputs_json(self, temp_plugin_env) -> None:

        """引数なしでJSON出力"""
        from interfaces.config_cli import main

        # argparseがsys.argvからパースするため、空のリストをセット
        test_args = ["cli.py"]
        captured_output = StringIO()
        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main(plugin_root=temp_plugin_env.plugin_root)

        output = captured_output.getvalue()

        # JSONとしてパース可能か検証
        parsed = json.loads(output)
        assert isinstance(parsed, dict)
        assert "paths" in parsed or "base_dir" in parsed

    @pytest.mark.integration
    def test_main_show_paths_flag(self, temp_plugin_env, caplog: pytest.LogCaptureFixture) -> None:

        """--show-paths フラグで paths を表示"""
        import logging

        from interfaces.config_cli import main

        # argparseをモック
        test_args = ["cli.py", "--show-paths"]

        with patch("sys.argv", test_args), caplog.at_level(logging.INFO):
            main(plugin_root=temp_plugin_env.plugin_root)

        # show_paths() はログ出力する
        log_output = caplog.text
        assert "Plugin Root" in log_output or len(caplog.records) > 0

    @pytest.mark.integration
    def test_main_plugin_root_override(self, temp_plugin_env) -> None:

        """plugin_root 引数でルートをオーバーライド"""
        from interfaces.config_cli import main

        test_args = ["cli.py"]
        captured_output = StringIO()

        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main(plugin_root=temp_plugin_env.plugin_root)

        output = captured_output.getvalue()
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    @pytest.mark.integration
    def test_main_invalid_plugin_root_exits_1(self, tmp_path: Path) -> None:

        """無効なplugin_rootでexit code 1"""
        from interfaces.config_cli import main

        # 存在しないパス
        invalid_root = tmp_path / "nonexistent" / "path"
        test_args = ["cli.py", "--plugin-root", str(invalid_root)]
        captured_stderr = StringIO()

        with patch("sys.argv", test_args), patch("sys.stderr", captured_stderr):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 1
        assert "[ERROR]" in captured_stderr.getvalue()

    @pytest.mark.integration
    def test_json_output_format(self, temp_plugin_env) -> None:

        """JSON出力フォーマットの検証"""
        from interfaces.config_cli import main

        test_args = ["cli.py"]
        captured_output = StringIO()

        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main(plugin_root=temp_plugin_env.plugin_root)

        output = captured_output.getvalue()
        json.loads(output)  # JSONとしてパース可能であることを確認

        # indent=2 でフォーマットされているか
        assert "\n" in output  # 改行があること
        assert "  " in output  # インデントがあること

    @pytest.mark.integration
    def test_main_with_args_plugin_root(self, temp_plugin_env) -> None:

        """--plugin-root 引数が正しく処理される"""
        from interfaces.config_cli import main

        test_args = ["cli.py", "--plugin-root", str(temp_plugin_env.plugin_root)]
        captured_output = StringIO()

        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main()

        output = captured_output.getvalue()
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    @pytest.mark.unit
    def test_cli_module_has_main(self) -> None:

        """cli モジュールに main 関数が存在"""
        from interfaces import config_cli

        assert hasattr(config_cli, "main")
        assert callable(config_cli.main)

    @pytest.mark.unit
    def test_cli_can_be_run_as_module(self) -> None:

        """__main__ ブロックが存在"""
        import inspect

        import interfaces.config_cli as cli_module

        source = inspect.getsource(cli_module)
        assert 'if __name__ == "__main__"' in source

    @pytest.mark.integration
    def test_unicode_in_output(self, temp_plugin_env) -> None:

        """出力にUnicodeが含まれても正しく処理される"""
        from interfaces.config_cli import main

        test_args = ["cli.py"]
        captured_output = StringIO()

        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main(plugin_root=temp_plugin_env.plugin_root)

        output = captured_output.getvalue()
        # ensure_ascii=False なので日本語があればそのまま出力される
        parsed = json.loads(output)
        assert isinstance(parsed, dict)
