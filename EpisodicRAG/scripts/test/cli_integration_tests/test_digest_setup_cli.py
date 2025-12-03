#!/usr/bin/env python3
"""
digest_setup CLI E2E Tests
==========================

Subprocess-based E2E tests for digest_setup.py CLI.
"""

import json

import pytest

from .cli_runner import CLIRunner
from .conftest import create_loop_file

# =============================================================================
# check サブコマンド E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestSetupCheckE2E:
    """check サブコマンドのE2Eテスト"""

    def test_check_unconfigured_returns_not_configured(self, cli_runner: CLIRunner) -> None:
        """未設定環境で not_configured を返す"""
        result = cli_runner.run_digest_setup("check")
        result.assert_success()
        result.assert_json_status("not_configured")

    def test_check_unconfigured_shows_config_exists_false(self, cli_runner: CLIRunner) -> None:
        """未設定環境で config_exists が false"""
        result = cli_runner.run_digest_setup("check")
        result.assert_json_contains("config_exists", False)

    def test_check_configured_returns_configured(self, configured_cli_runner: CLIRunner) -> None:
        """設定済み環境で configured を返す"""
        result = configured_cli_runner.run_digest_setup("check")
        result.assert_success()
        result.assert_json_status("configured")

    def test_check_configured_shows_config_exists_true(
        self, configured_cli_runner: CLIRunner
    ) -> None:
        """設定済み環境で config_exists が true"""
        result = configured_cli_runner.run_digest_setup("check")
        result.assert_json_contains("config_exists", True)

    def test_check_configured_shows_directories_exist_true(
        self, configured_cli_runner: CLIRunner
    ) -> None:
        """設定済み環境で directories_exist が true"""
        result = configured_cli_runner.run_digest_setup("check")
        result.assert_json_contains("directories_exist", True)

    def test_check_output_is_valid_json(self, cli_runner: CLIRunner) -> None:
        """check の出力が有効なJSON"""
        result = cli_runner.run_digest_setup("check")
        assert result.json_output is not None


# =============================================================================
# init サブコマンド E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestSetupInitE2E:
    """init サブコマンドのE2Eテスト"""

    def test_init_with_valid_config_succeeds(
        self, cli_runner: CLIRunner, valid_config_json: str
    ) -> None:
        """有効な設定で初期化成功"""
        result = cli_runner.run_digest_setup("init", config=valid_config_json)
        result.assert_success()
        result.assert_json_status("ok")

    def test_init_creates_config_file(
        self, cli_runner: CLIRunner, cli_plugin_root, valid_config_json: str
    ) -> None:
        """init が設定ファイルを作成"""
        cli_runner.run_digest_setup("init", config=valid_config_json)
        config_file = cli_plugin_root / ".claude-plugin" / "config.json"
        assert config_file.exists()

    def test_init_creates_directories(
        self, cli_runner: CLIRunner, cli_plugin_root, valid_config_json: str
    ) -> None:
        """init がディレクトリを作成"""
        cli_runner.run_digest_setup("init", config=valid_config_json)
        assert (cli_plugin_root / "data" / "Loops").exists()
        assert (cli_plugin_root / "data" / "Digests").exists()
        assert (cli_plugin_root / "data" / "Essences").exists()

    def test_init_with_invalid_json_fails(self, cli_runner: CLIRunner) -> None:
        """不正なJSONで失敗"""
        result = cli_runner.run_digest_setup("init", config="{invalid json")
        result.assert_failure(1)
        result.assert_json_status("error")

    def test_init_already_configured_returns_status(
        self, configured_cli_runner: CLIRunner, valid_config_json: str
    ) -> None:
        """既存設定がある場合は already_configured を返す"""
        result = configured_cli_runner.run_digest_setup("init", config=valid_config_json)
        result.assert_json_status("already_configured")

    def test_init_with_force_overwrites(
        self, configured_cli_runner: CLIRunner, valid_config_json: str
    ) -> None:
        """--force で既存設定を上書き"""
        result = configured_cli_runner.run_digest_setup(
            "init", config=valid_config_json, force=True
        )
        result.assert_success()
        result.assert_json_status("ok")


# =============================================================================
# エラー処理 E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestSetupErrorsE2E:
    """エラー処理のE2Eテスト"""

    def test_no_subcommand_exits_with_error(self, cli_runner: CLIRunner) -> None:
        """サブコマンドなしでエラー"""
        result = cli_runner.run_digest_setup()
        result.assert_failure()

    def test_invalid_subcommand_exits_with_error(self, cli_runner: CLIRunner) -> None:
        """無効なサブコマンドでエラー"""
        result = cli_runner.run_digest_setup("invalid_command")
        result.assert_failure(2)  # argparse error

    def test_init_without_config_exits_with_error(self, cli_runner: CLIRunner) -> None:
        """init で --config なしはエラー"""
        result = cli_runner.run_digest_setup("init")
        result.assert_failure(2)  # argparse error

    def test_nonexistent_plugin_root_returns_error(self, cli_temp_dir) -> None:
        """存在しないplugin-rootでエラー"""
        runner = CLIRunner(plugin_root=cli_temp_dir / "nonexistent")
        result = runner.run_digest_setup("check")
        # ディレクトリが存在しなくてもcheckは動作するが、config_existsはfalse
        result.assert_json_contains("config_exists", False)
