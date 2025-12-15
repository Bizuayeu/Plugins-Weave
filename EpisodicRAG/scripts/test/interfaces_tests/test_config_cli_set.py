#!/usr/bin/env python3
"""
ConfigEditor CLI set コマンドテスト
===================================

set サブコマンドの追加CLIテスト。
test_digest_config.py から分割。
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestConfigCLISetCommandExtended(unittest.TestCase):
    """set サブコマンドの追加CLIテスト"""

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
        self._create_config()

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        # 環境変数をリセット
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self) -> None:
        """設定ファイルを作成（永続化ディレクトリに）"""
        config_data = {
            "base_dir": str(self.plugin_root),
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5, "monthly_threshold": 5},
        }
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_set_missing_key_exits_error(self) -> None:
        """set で --key がない場合にエラー"""
        with patch(
            "sys.argv",
            ["digest_config.py", "set", "--value", "7"],
        ):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main

                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_set_missing_value_exits_error(self) -> None:
        """set で --value がない場合にエラー"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "levels.weekly_threshold",
            ],
        ):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main

                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_set_deeply_nested_key(self) -> None:
        """set で深くネストされたキーを設定"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "paths.loops_dir",
                "--value",
                "custom/Loops",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert result["new_value"] == "custom/Loops"

    @pytest.mark.unit
    def test_set_creates_intermediate_keys(self) -> None:
        """set が中間キーを作成する"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "new_section.new_key",
                "--value",
                "new_value",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"

        # ファイルを確認（永続化ディレクトリから）
        with open(self.persistent_config / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert saved_config["new_section"]["new_key"] == "new_value"

    @pytest.mark.unit
    def test_set_boolean_true(self) -> None:
        """set で true を設定"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "some_flag",
                "--value",
                "true",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["new_value"] is True

    @pytest.mark.unit
    def test_set_boolean_false(self) -> None:
        """set で false を設定"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "some_flag",
                "--value",
                "false",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["new_value"] is False

    @pytest.mark.unit
    def test_set_null_value(self) -> None:
        """set で null を設定"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "paths.identity_file_path",
                "--value",
                "null",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["new_value"] is None

    @pytest.mark.unit
    def test_set_negative_integer(self) -> None:
        """set で負の整数を設定"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "some_value",
                "--value",
                "-10",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["new_value"] == -10

    @pytest.mark.unit
    def test_set_threshold_invalid_string_exits_error(self) -> None:
        """set で閾値に無効な文字列を設定するとエラー"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "levels.weekly_threshold",
                "--value",
                "not_a_number",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"
                assert "integer" in result["error"].lower()

    @pytest.mark.unit
    def test_set_output_shows_old_value(self) -> None:
        """set が古い値を表示"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "set",
                "--key",
                "levels.weekly_threshold",
                "--value",
                "10",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["old_value"] == 5
                assert result["new_value"] == 10


if __name__ == "__main__":
    unittest.main()
