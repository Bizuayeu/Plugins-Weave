#!/usr/bin/env python3
"""
DigestAuto CLI 基本・引数テスト
===============================

CLI エントリーポイントと引数バリデーションのテスト。
test_digest_auto.py から分割。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestDigestAutoCLI(unittest.TestCase):
    """CLI エントリーポイントのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self) -> None:

        """最小のプラグイン構造を作成"""
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {"weekly": {"overall_digest": None}},
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

    @pytest.mark.unit
    def test_main_json_output(self) -> None:

        """JSON出力が動作する"""
        with patch(
            "sys.argv", ["digest_auto.py", "--output", "json", "--plugin-root", str(self.plugin_root)]
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                assert mock_print.called
                # JSON形式であることを確認
                call_args = mock_print.call_args[0][0]
                parsed = json.loads(call_args)
                assert "status" in parsed

    @pytest.mark.unit
    def test_main_text_output(self) -> None:

        """テキスト出力が動作する"""
        with patch(
            "sys.argv", ["digest_auto.py", "--output", "text", "--plugin-root", str(self.plugin_root)]
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                assert mock_print.called

    @pytest.mark.unit
    def test_main_help_exits_zero(self) -> None:

        """--help で exit code 0"""
        with patch("sys.argv", ["digest_auto.py", "--help"]):
            with patch("sys.stdout"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_auto import main

                    main()
                assert exc_info.value.code == 0


class TestDigestAutoCLIArgumentValidation(unittest.TestCase):
    """CLI引数バリデーションのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self) -> None:

        """最小のプラグイン構造を作成"""
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {"weekly": {"overall_digest": None}},
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

    @pytest.mark.unit
    def test_invalid_output_format_exits_with_error(self) -> None:

        """無効な --output 形式でエラー終了"""
        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "invalid_format",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_auto import main
                    main()
                assert exc_info.value.code == 2  # argparse error

    @pytest.mark.unit
    def test_default_output_is_json(self) -> None:

        """--output 省略時はJSONがデフォルト"""
        with patch("sys.argv", [
            "digest_auto.py",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_plugin_root_without_config_exits_with_error(self) -> None:

        """config.json がない場合にエラー"""

        # config.json を削除
        (self.plugin_root / ".claude-plugin" / "config.json").unlink()

        with patch("sys.argv", [
            "digest_auto.py",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                # Note: digest_auto returns exit code 0 even with status="error"
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_nonexistent_plugin_root(self) -> None:

        """存在しない plugin-root でエラー"""

        with patch("sys.argv", [
            "digest_auto.py",
            "--plugin-root", "/nonexistent/path/to/plugin"
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                # Note: digest_auto returns exit code 0 even with status="error"
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_output_json_option(self) -> None:

        """--output json オプションが動作"""
        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert "status" in result

    @pytest.mark.unit
    def test_output_text_option(self) -> None:

        """--output text オプションが動作（format_text_reportを直接テスト）"""
        from interfaces.digest_auto import AnalysisResult, format_text_report

        result = AnalysisResult(status="ok")
        formatted = format_text_report(result)

        # テキスト形式であることを確認
        assert "```text" in formatted
        assert "━" in formatted

    @pytest.mark.unit
    def test_unknown_option_exits_with_error(self) -> None:

        """未知のオプションでエラー終了"""
        with patch("sys.argv", [
            "digest_auto.py",
            "--unknown-option",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stderr"):
                with pytest.raises(SystemExit) as exc_info:
                    from interfaces.digest_auto import main
                    main()
                assert exc_info.value.code == 2

    @pytest.mark.unit
    def test_positional_args_accepted(self) -> None:

        """位置引数はargparseで定義されていないためエラー（または無視）"""

        # argparseの設定によっては位置引数がエラーになる
        with patch("sys.argv", [
            "digest_auto.py",
            "unexpected_positional",
            "--plugin-root", str(self.plugin_root)
        ]):
            with patch("sys.stderr"):
                # 位置引数がエラーになるかどうかを確認
                try:
                    from interfaces.digest_auto import main
                    with patch("builtins.print"):
                        main()
                except SystemExit as e:
                    # argparseがエラーを返す場合
                    assert e.code == 2


if __name__ == "__main__":
    unittest.main()
