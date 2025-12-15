#!/usr/bin/env python3
"""
SetupManager CLI init コマンドテスト
====================================

init サブコマンドのCLIテスト。
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


class TestSetupCLIInitCommand(unittest.TestCase):
    """init サブコマンドのCLIテスト"""

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
        self._create_templates()

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        # 環境変数をリセット
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_templates(self) -> None:
        """テンプレートファイルを作成"""
        template_dir = self.plugin_root / ".claude-plugin"
        grand_template = {"metadata": {"last_updated": "", "version": "1.0"}, "major_digests": {}}
        with open(template_dir / "GrandDigest.template.txt", "w", encoding="utf-8") as f:
            json.dump(grand_template, f)
        shadow_template = {"metadata": {"last_updated": "", "version": "1.0"}, "latest_digests": {}}
        with open(template_dir / "ShadowGrandDigest.template.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_template, f)
        times_template = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(template_dir / "last_digest_times.template.json", "w", encoding="utf-8") as f:
            json.dump(times_template, f)

    def _get_valid_config_json(self):
        """有効な設定JSONを返す"""
        return json.dumps(
            {
                "base_dir": str(self.plugin_root),
                "paths": {
                    "loops_dir": "data/Loops",
                    "digests_dir": "data/Digests",
                    "essences_dir": "data/Essences",
                },
                "levels": {
                    "weekly_threshold": 5,
                    "monthly_threshold": 5,
                    "quarterly_threshold": 3,
                    "annual_threshold": 4,
                    "triennial_threshold": 3,
                    "decadal_threshold": 3,
                    "multi_decadal_threshold": 3,
                    "centurial_threshold": 4,
                },
            }
        )

    @pytest.mark.unit
    def test_init_with_valid_config_json(self) -> None:
        """init --config で有効なJSONを渡す"""
        config_json = self._get_valid_config_json()

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert result["created"] is not None

    @pytest.mark.unit
    def test_init_with_invalid_json_exits_error(self) -> None:
        """init --config に不正なJSONを渡すとエラー"""
        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                "{invalid json",
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_init_with_missing_paths_exits_error(self) -> None:
        """init --config で paths がないとエラー"""
        config_json = json.dumps(
            {
                "base_dir": str(self.plugin_root),
                "levels": {"weekly_threshold": 5},
            }
        )

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"
                assert "paths" in result["error"].lower()

    @pytest.mark.unit
    def test_init_with_missing_levels_exits_error(self) -> None:
        """init --config で levels がないとエラー"""
        config_json = json.dumps(
            {
                "base_dir": str(self.plugin_root),
                "paths": {
                    "loops_dir": "data/Loops",
                    "digests_dir": "data/Digests",
                    "essences_dir": "data/Essences",
                },
            }
        )

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"
                assert "levels" in result["error"].lower()

    @pytest.mark.unit
    def test_init_with_invalid_threshold_exits_error(self) -> None:
        """init --config で無効な閾値を渡すとエラー"""
        config_json = json.dumps(
            {
                "base_dir": str(self.plugin_root),
                "paths": {
                    "loops_dir": "data/Loops",
                    "digests_dir": "data/Digests",
                    "essences_dir": "data/Essences",
                },
                "levels": {
                    "weekly_threshold": -1,  # 無効な値
                    "monthly_threshold": 5,
                    "quarterly_threshold": 3,
                    "annual_threshold": 4,
                    "triennial_threshold": 3,
                    "decadal_threshold": 3,
                    "multi_decadal_threshold": 3,
                    "centurial_threshold": 4,
                },
            }
        )

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_init_creates_directories(self) -> None:
        """init がディレクトリを作成する"""
        config_json = self._get_valid_config_json()

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print"):
                main()

        # ディレクトリが作成されていることを確認
        assert (self.plugin_root / "data" / "Loops").exists()
        assert (self.plugin_root / "data" / "Digests" / "1_Weekly").exists()
        assert (self.plugin_root / "data" / "Essences").exists()

    @pytest.mark.unit
    def test_init_creates_config_file(self) -> None:
        """init が設定ファイルを作成する（永続化ディレクトリに）"""
        config_json = self._get_valid_config_json()

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print"):
                main()

        # 設定ファイルが永続化ディレクトリに作成されていることを確認
        assert (self.persistent_config / "config.json").exists()

    @pytest.mark.unit
    def test_init_without_force_fails_when_exists(self) -> None:
        """既存設定がある場合、force なしで失敗する"""
        # 既存の設定ファイルを作成（永続化ディレクトリに）
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

        config_json = self._get_valid_config_json()

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "already_configured"

    @pytest.mark.unit
    def test_init_with_force_overwrites_existing(self) -> None:
        """既存設定がある場合でも force で上書きする"""
        # 既存の設定ファイルを作成（永続化ディレクトリに）
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump({"old": "config"}, f)

        config_json = self._get_valid_config_json()

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
                "--force",
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"

    @pytest.mark.unit
    def test_init_detects_external_paths(self) -> None:
        """init が外部パスを検出する"""
        config_json = json.dumps(
            {
                "base_dir": "~/external/path",
                "paths": {
                    "loops_dir": "data/Loops",
                    "digests_dir": "data/Digests",
                    "essences_dir": "data/Essences",
                },
                "levels": {
                    "weekly_threshold": 5,
                    "monthly_threshold": 5,
                    "quarterly_threshold": 3,
                    "annual_threshold": 4,
                    "triennial_threshold": 3,
                    "decadal_threshold": 3,
                    "multi_decadal_threshold": 3,
                    "centurial_threshold": 4,
                },
            }
        )

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"
                assert len(result["external_paths_detected"]) > 0

    @pytest.mark.unit
    def test_init_output_is_valid_json(self) -> None:
        """init の出力が有効なJSON"""
        config_json = self._get_valid_config_json()

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                # JSONとしてパース可能であることを確認
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_init_output_contains_created_info(self) -> None:
        """init の出力が作成情報を含む"""
        config_json = self._get_valid_config_json()

        with patch(
            "sys.argv",
            [
                "digest_setup.py",
                "init",
                "--config",
                config_json,
            ],
        ):
            from interfaces.digest_setup import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert "created" in result
                assert "config_file" in result["created"]
                assert "directories" in result["created"]
                assert "files" in result["created"]


if __name__ == "__main__":
    unittest.main()
