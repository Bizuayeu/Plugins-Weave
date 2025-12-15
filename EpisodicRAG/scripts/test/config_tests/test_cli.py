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
from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict, List, Tuple

    from test_helpers import TempPluginEnvironment

    from application.config import DigestConfig
    from application.grand import GrandDigestManager, ShadowGrandDigestManager
    from application.shadow import FileDetector, ShadowIO, ShadowTemplate
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.tracking import DigestTimesTracker
    from domain.types.level import LevelHierarchyEntry


import pytest


class TestCliMain:
    """config.cli.main() 関数のテスト"""

    @pytest.mark.integration
    def test_main_no_arguments_outputs_json(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """引数なしでJSON出力"""
        from interfaces.config_cli import main

        # argparseがsys.argvからパースするため、空のリストをセット
        test_args = ["cli.py"]
        captured_output = StringIO()
        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main()

        output = captured_output.getvalue()

        # JSONとしてパース可能か検証
        parsed = json.loads(output)
        assert isinstance(parsed, dict)
        assert "paths" in parsed or "base_dir" in parsed

    @pytest.mark.integration
    def test_main_show_paths_flag(
        self, temp_plugin_env: "TempPluginEnvironment", caplog: pytest.LogCaptureFixture
    ) -> None:
        """--show-paths フラグで paths を表示"""
        import logging

        from interfaces.config_cli import main

        # argparseをモック
        test_args = ["cli.py", "--show-paths"]

        with patch("sys.argv", test_args), caplog.at_level(logging.INFO):
            main()

        # show_paths() はログ出力する
        log_output = caplog.text
        assert len(caplog.records) > 0 or log_output != ""

    @pytest.mark.integration
    def test_main_outputs_json(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """main() がJSON出力する"""
        from interfaces.config_cli import main

        test_args = ["cli.py"]
        captured_output = StringIO()

        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main()

        output = captured_output.getvalue()
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    @pytest.mark.integration
    def test_json_output_format(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """JSON出力フォーマットの検証"""
        from interfaces.config_cli import main

        test_args = ["cli.py"]
        captured_output = StringIO()

        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main()

        output = captured_output.getvalue()
        json.loads(output)  # JSONとしてパース可能であることを確認

        # indent=2 でフォーマットされているか
        assert "\n" in output  # 改行があること
        assert "  " in output  # インデントがあること

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
    def test_unicode_in_output(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """出力にUnicodeが含まれても正しく処理される"""
        from interfaces.config_cli import main

        test_args = ["cli.py"]
        captured_output = StringIO()

        with patch("sys.argv", test_args), patch("sys.stdout", captured_output):
            main()

        output = captured_output.getvalue()
        # ensure_ascii=False なので日本語があればそのまま出力される
        parsed = json.loads(output)
        assert isinstance(parsed, dict)
