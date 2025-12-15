#!/usr/bin/env python3
"""
SetupManager CLI check コマンドテスト
=====================================

check サブコマンドとコマンドなしのテスト。
test_digest_setup.py から分割。
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSetupCLI(unittest.TestCase):
    """CLI エントリーポイントのテスト"""

    def setUp(self) -> None:
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        # 永続化設定ディレクトリを作成
        self.persistent_config = self.plugin_root / ".persistent_config"
        self.persistent_config.mkdir(parents=True)
        # 環境変数を設定
        self._old_env = os.environ.get("EPISODICRAG_CONFIG_DIR")
        os.environ["EPISODICRAG_CONFIG_DIR"] = str(self.persistent_config)

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        # 環境変数をリセット
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_main_check_command(self) -> None:
        """check コマンドが動作する"""
        with patch("sys.argv", ["digest_setup.py", "check"]):
            from interfaces.digest_setup import main

            # 出力をキャプチャ
            with patch("builtins.print") as mock_print:
                main()
                # JSON が出力されることを確認
                assert mock_print.called

    @pytest.mark.unit
    def test_main_help_exits_zero(self) -> None:
        """--help で exit code 0"""
        with patch("sys.argv", ["digest_setup.py", "--help"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_setup import main

                    main()
                assert exc_info.value.code == 0


class TestSetupCLICheckCommandExtended(unittest.TestCase):
    """check サブコマンドの追加CLIテスト"""

    def setUp(self) -> None:
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        # 永続化設定ディレクトリを作成
        self.persistent_config = self.plugin_root / ".persistent_config"
        self.persistent_config.mkdir(parents=True)
        # 環境変数を設定
        self._old_env = os.environ.get("EPISODICRAG_CONFIG_DIR")
        os.environ["EPISODICRAG_CONFIG_DIR"] = str(self.persistent_config)

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        # 環境変数をリセット
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_check_not_configured_output_format(self) -> None:
        """check の not_configured 出力形式"""
        with patch("sys.argv", ["digest_setup.py", "check"]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "not_configured"
                assert "config_exists" in result
                assert "directories_exist" in result
                assert "message" in result

    @pytest.mark.unit
    def test_check_configured_output_format(self) -> None:
        """check の configured 出力形式"""
        # 設定ファイルとディレクトリを作成（永続化ディレクトリに）
        config_data = {
            "base_dir": str(self.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
        }
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)

        with patch("sys.argv", ["digest_setup.py", "check"]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "configured"
                assert result["config_exists"] is True
                assert result["directories_exist"] is True

    @pytest.mark.unit
    def test_check_partial_output_format(self) -> None:
        """check の partial 出力形式"""
        # 設定ファイルのみ作成（永続化ディレクトリに、ディレクトリなし）
        config_data = {
            "base_dir": str(self.plugin_root),
            "paths": {"loops_dir": "data/Loops"},
        }
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        with patch("sys.argv", ["digest_setup.py", "check"]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "partial"
                assert result["config_exists"] is True
                assert result["directories_exist"] is False

    @pytest.mark.unit
    def test_check_with_corrupted_config(self) -> None:
        """check で破損した設定ファイルを処理"""
        # 破損したJSONファイルを作成（永続化ディレクトリに）
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        with patch("sys.argv", ["digest_setup.py", "check"]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                # エラーにならずにpartialを返す
                assert result["status"] in ["partial", "not_configured"]
                assert result["config_exists"] is True

    @pytest.mark.unit
    def test_check_output_is_valid_json(self) -> None:
        """check の出力が有効なJSON"""
        with patch("sys.argv", ["digest_setup.py", "check"]):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)


class TestSetupCLINoCommand(unittest.TestCase):
    """コマンドなしの場合のテスト"""

    def setUp(self) -> None:
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        # 永続化設定ディレクトリを作成
        self.persistent_config = self.plugin_root / ".persistent_config"
        self.persistent_config.mkdir(parents=True)
        # 環境変数を設定
        self._old_env = os.environ.get("EPISODICRAG_CONFIG_DIR")
        os.environ["EPISODICRAG_CONFIG_DIR"] = str(self.persistent_config)

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        # 環境変数をリセット
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_no_command_exits_with_code_1(self) -> None:
        """コマンドなしで exit code 1"""
        with patch("sys.argv", ["digest_setup.py"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_setup import main

                    main()
                assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_invalid_command_exits_with_error(self) -> None:
        """無効なコマンドでエラー"""
        with patch("sys.argv", ["digest_setup.py", "invalid_command"]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_setup import main

                    main()
                assert exc_info.value.code == 2  # argparse error

    @pytest.mark.unit
    def test_init_missing_config_flag_exits_error(self) -> None:
        """init で --config フラグがない場合にエラー"""
        with patch("sys.argv", ["digest_setup.py", "init"]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_setup import main

                    main()
                assert exc_info.value.code == 2  # argparse error


if __name__ == "__main__":
    unittest.main()
