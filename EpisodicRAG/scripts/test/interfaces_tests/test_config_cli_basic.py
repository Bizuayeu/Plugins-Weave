#!/usr/bin/env python3
"""
ConfigEditor CLI 基本テスト
===========================

出力ヘルパー、基本CLI、updateコマンドのテスト。
test_digest_config.py から分割。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestOutputHelpers(unittest.TestCase):
    """出力ヘルパー関数のテスト"""

    @pytest.mark.unit
    def test_output_json_formats_correctly(self):
        """output_json が正しいJSON形式で出力する"""
        from interfaces.digest_config import output_json

        test_data = {"status": "ok", "message": "Test"}

        with patch("builtins.print") as mock_print:
            output_json(test_data)
            mock_print.assert_called_once()
            # 出力がJSON形式であることを確認
            call_args = mock_print.call_args[0][0]
            parsed = json.loads(call_args)
            assert parsed["status"] == "ok"

    @pytest.mark.unit
    def test_output_error_basic(self):
        """output_error が基本的なエラーを出力する"""
        from interfaces.digest_config import output_error

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                output_error("Test error")

            assert exc_info.value.code == 1
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            parsed = json.loads(call_args)
            assert parsed["status"] == "error"
            assert parsed["error"] == "Test error"

    @pytest.mark.unit
    def test_output_error_with_details(self):
        """output_error が詳細情報付きでエラーを出力する"""
        from interfaces.digest_config import output_error

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit):
                output_error("Test error", details={"action": "Run setup"})

            call_args = mock_print.call_args[0][0]
            parsed = json.loads(call_args)
            assert parsed["status"] == "error"
            assert parsed["details"]["action"] == "Run setup"


class TestConfigCLI(unittest.TestCase):
    """CLI エントリーポイントのテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self):
        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_main_show_command(self):
        """show コマンドが動作する"""
        with patch("sys.argv", ["digest_config.py", "--plugin-root", str(self.plugin_root), "show"]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                assert mock_print.called

    @pytest.mark.unit
    def test_main_set_command(self):
        """set コマンドが動作する"""
        with patch(
            "sys.argv",
            [
                "digest_config.py",
                "--plugin-root",
                str(self.plugin_root),
                "set",
                "--key",
                "levels.weekly_threshold",
                "--value",
                "7",
            ],
        ):
            from interfaces.digest_config import main

            with patch("builtins.print"):
                main()

        # 値が更新されていることを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        assert config["levels"]["weekly_threshold"] == 7

    @pytest.mark.unit
    def test_main_help_exits_zero(self):
        """--help で exit code 0"""
        with patch("sys.argv", ["digest_config.py", "--help"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main

                    main()
                assert exc_info.value.code == 0


class TestConfigCLIUpdateCommand(unittest.TestCase):
    """update サブコマンドのCLIテスト"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self):
        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "trusted_external_paths": [],
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_update_with_valid_json(self):
        """update --config で有効なJSONを渡す"""
        config_json = json.dumps({"base_dir": "../new_path"})

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert "base_dir" in result["updated_keys"]

    @pytest.mark.unit
    def test_update_with_invalid_json_exits_error(self):
        """update --config に不正なJSONを渡すとエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", "{invalid json"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_update_with_empty_json_object(self):
        """update --config で空のJSONオブジェクト"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", "{}"
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert result["updated_keys"] == []

    @pytest.mark.unit
    def test_update_preserves_existing_keys(self):
        """update が既存キーを保持する"""
        config_json = json.dumps({"base_dir": "../updated"})

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print"):
                main()

        # levels キーが保持されていることを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert "levels" in saved_config
        assert saved_config["levels"]["weekly_threshold"] == 5

    @pytest.mark.unit
    def test_update_missing_config_flag_exits_error(self):
        """update で --config フラグがない場合にエラー"""
        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update"
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_config import main
                    main()
                assert exc_info.value.code == 2  # argparse error

    @pytest.mark.unit
    def test_update_output_is_valid_json(self):
        """update の出力が有効なJSON"""
        config_json = json.dumps({"base_dir": "."})

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_update_with_partial_config(self):
        """update で一部のキーのみ更新"""
        config_json = json.dumps({
            "levels": {"weekly_threshold": 10}
        })

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"

        # 更新されていることを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert saved_config["levels"]["weekly_threshold"] == 10

    @pytest.mark.unit
    def test_update_reports_updated_keys(self):
        """update が更新されたキーを報告"""
        config_json = json.dumps({
            "base_dir": "../new",
            "levels": {"weekly_threshold": 7}
        })

        with patch("sys.argv", [
            "digest_config.py",
            "--plugin-root", str(self.plugin_root),
            "update",
            "--config", config_json
        ]):
            from interfaces.digest_config import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert "base_dir" in result["updated_keys"]
                assert "levels" in result["updated_keys"]


if __name__ == "__main__":
    unittest.main()
