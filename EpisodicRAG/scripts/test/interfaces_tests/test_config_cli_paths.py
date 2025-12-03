#!/usr/bin/env python3
"""
ConfigEditor CLI trusted-paths コマンドテスト
=============================================

trusted-paths サブコマンドとコマンドなしのテスト。
test_digest_config.py から分割。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestConfigCLITrustedPathsCommand(unittest.TestCase):
    """trusted-paths サブコマンドのCLIテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self) -> None:

        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "data/Loops",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_trusted_paths_list_empty(self) -> None:

        """trusted-paths list で空リスト"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "list"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert result["count"] == 0
                assert result["trusted_external_paths"] == []

    @pytest.mark.unit
    def test_trusted_paths_list_with_paths(self) -> None:

        """trusted-paths list でパスあり"""
        # 先にパスを追加
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": ["~/path1", "~/path2"],
            "paths": {"loops_dir": "data/Loops"},
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "list"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["count"] == 2

    @pytest.mark.unit
    def test_trusted_paths_add_valid_absolute_path(self) -> None:

        """trusted-paths add で有効な絶対パス"""
        # Windowsでも動作するよう、tempディレクトリを使用
        abs_path = str(self.plugin_root / "external")

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", abs_path
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert abs_path in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_trusted_paths_add_tilde_path(self) -> None:

        """trusted-paths add で ~ パス"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", "~/DEV/production"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "~/DEV/production" in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_trusted_paths_add_relative_path_rejected(self) -> None:

        """trusted-paths add で相対パスを拒否"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", "relative/path"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_trusted_paths_add_duplicate_handled(self) -> None:

        """trusted-paths add で重複を処理"""
        # 先にパスを追加
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", "~/DEV/test"
        ]):
            from interfaces.digest_config import main
            with patch("builtins.print"):
                main()

        # 同じパスを再度追加
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "add", "~/DEV/test"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "already exists" in result["message"].lower()

    @pytest.mark.unit
    def test_trusted_paths_remove_existing(self) -> None:

        """trusted-paths remove で既存パス削除"""
        # 先にパスを追加
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": ["~/DEV/production"],
            "paths": {"loops_dir": "data/Loops"},
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "remove", "~/DEV/production"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "~/DEV/production" not in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_trusted_paths_remove_nonexistent_error(self) -> None:

        """trusted-paths remove で存在しないパスはエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "remove", "~/nonexistent"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_trusted_paths_no_subcommand_lists(self) -> None:

        """trusted-paths でサブコマンドなしはリスト表示"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "trusted_external_paths" in result

    @pytest.mark.unit
    def test_trusted_paths_output_is_valid_json(self) -> None:

        """trusted-paths の出力が有効なJSON"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "trusted-paths", "list"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)


class TestConfigCLINoCommand(unittest.TestCase):
    """コマンドなしの場合のテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        config_data = {"base_dir": ".", "levels": {"weekly_threshold": 5}}
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_no_command_exits_with_code_1(self) -> None:

        """コマンドなしで exit code 1"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main
                    main()
                assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_invalid_command_exits_with_error(self) -> None:

        """無効なコマンドでエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "invalid_command"
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main
                    main()
                assert exc_info.value.code == 2  # argparse error


if __name__ == "__main__":
    unittest.main()
