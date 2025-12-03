#!/usr/bin/env python3
"""
digest_config CLI E2E Tests
===========================

Subprocess-based E2E tests for digest_config.py CLI.
"""

import json

import pytest

from .cli_runner import CLIRunner

# =============================================================================
# show サブコマンド E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestConfigShowE2E:
    """show サブコマンドのE2Eテスト"""

    def test_show_returns_current_config(self, configured_cli_runner: CLIRunner) -> None:
        """show が現在の設定を返す"""
        result = configured_cli_runner.run_digest_config("show")
        result.assert_success()
        result.assert_json_status("ok")

    def test_show_contains_base_dir(self, configured_cli_runner: CLIRunner) -> None:
        """show の出力に base_dir が含まれる"""
        result = configured_cli_runner.run_digest_config("show")
        assert "config" in result.json_output
        assert "base_dir" in result.json_output["config"]

    def test_show_contains_levels(self, configured_cli_runner: CLIRunner) -> None:
        """show の出力に levels が含まれる"""
        result = configured_cli_runner.run_digest_config("show")
        assert "levels" in result.json_output["config"]

    def test_show_without_config_returns_error(self, cli_runner: CLIRunner) -> None:
        """設定なしで show はエラー"""
        result = cli_runner.run_digest_config("show")
        result.assert_failure()
        result.assert_json_status("error")


# =============================================================================
# set サブコマンド E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestConfigSetE2E:
    """set サブコマンドのE2Eテスト"""

    def test_set_updates_value(self, configured_cli_runner: CLIRunner) -> None:
        """set が値を更新"""
        result = configured_cli_runner.run_digest_config(
            "set", key="levels.weekly_threshold", value="10"
        )
        result.assert_success()
        result.assert_json_status("ok")
        assert result.json_output["new_value"] == 10

    def test_set_shows_old_value(self, configured_cli_runner: CLIRunner) -> None:
        """set が古い値を表示"""
        result = configured_cli_runner.run_digest_config(
            "set", key="levels.weekly_threshold", value="10"
        )
        assert "old_value" in result.json_output

    def test_set_deeply_nested_key(self, configured_cli_runner: CLIRunner) -> None:
        """set でネストされたキーを更新"""
        result = configured_cli_runner.run_digest_config(
            "set", key="paths.loops_dir", value="custom/Loops"
        )
        result.assert_success()
        assert result.json_output["new_value"] == "custom/Loops"

    def test_set_boolean_true(self, configured_cli_runner: CLIRunner) -> None:
        """set で true を設定"""
        result = configured_cli_runner.run_digest_config("set", key="some_flag", value="true")
        result.assert_success()
        assert result.json_output["new_value"] is True

    def test_set_boolean_false(self, configured_cli_runner: CLIRunner) -> None:
        """set で false を設定"""
        result = configured_cli_runner.run_digest_config("set", key="some_flag", value="false")
        result.assert_success()
        assert result.json_output["new_value"] is False

    def test_set_missing_key_fails(self, configured_cli_runner: CLIRunner) -> None:
        """set で --key なしはエラー"""
        result = configured_cli_runner.run_digest_config("set", value="10")
        result.assert_failure(2)

    def test_set_missing_value_fails(self, configured_cli_runner: CLIRunner) -> None:
        """set で --value なしはエラー"""
        result = configured_cli_runner.run_digest_config("set", key="levels.weekly_threshold")
        result.assert_failure(2)


# =============================================================================
# update サブコマンド E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestConfigUpdateE2E:
    """update サブコマンドのE2Eテスト"""

    def test_update_with_valid_json(self, configured_cli_runner: CLIRunner) -> None:
        """update で有効なJSONを渡す"""
        config_json = json.dumps({"base_dir": "../updated"})
        result = configured_cli_runner.run_digest_config("update", config=config_json)
        result.assert_success()
        result.assert_json_status("ok")

    def test_update_reports_updated_keys(self, configured_cli_runner: CLIRunner) -> None:
        """update が更新されたキーを報告"""
        config_json = json.dumps({"base_dir": "../new"})
        result = configured_cli_runner.run_digest_config("update", config=config_json)
        assert "updated_keys" in result.json_output
        assert "base_dir" in result.json_output["updated_keys"]

    def test_update_with_empty_json(self, configured_cli_runner: CLIRunner) -> None:
        """update で空のJSONオブジェクト"""
        result = configured_cli_runner.run_digest_config("update", config="{}")
        result.assert_success()
        assert result.json_output["updated_keys"] == []

    def test_update_with_invalid_json_fails(self, configured_cli_runner: CLIRunner) -> None:
        """update で不正なJSONはエラー"""
        result = configured_cli_runner.run_digest_config("update", config="{invalid")
        result.assert_failure(1)
        result.assert_json_status("error")

    def test_update_missing_config_flag_fails(self, configured_cli_runner: CLIRunner) -> None:
        """update で --config なしはエラー"""
        result = configured_cli_runner.run_digest_config("update")
        result.assert_failure(2)


# =============================================================================
# trusted-paths サブコマンド E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestConfigTrustedPathsE2E:
    """trusted-paths サブコマンドのE2Eテスト"""

    def test_trusted_paths_list_empty(self, configured_cli_runner: CLIRunner) -> None:
        """trusted-paths list で空リスト"""
        result = configured_cli_runner.run_digest_config("trusted-paths", "list")
        result.assert_success()
        assert result.json_output["count"] == 0

    def test_trusted_paths_add_tilde_path(self, configured_cli_runner: CLIRunner) -> None:
        """trusted-paths add で ~ パスを追加"""
        result = configured_cli_runner.run_digest_config("trusted-paths", "add", "~/DEV/production")
        result.assert_success()
        assert "~/DEV/production" in result.json_output["trusted_external_paths"]

    def test_trusted_paths_add_relative_path_rejected(
        self, configured_cli_runner: CLIRunner
    ) -> None:
        """trusted-paths add で相対パスを拒否"""
        result = configured_cli_runner.run_digest_config("trusted-paths", "add", "relative/path")
        result.assert_json_status("error")

    def test_trusted_paths_remove_nonexistent_error(self, configured_cli_runner: CLIRunner) -> None:
        """trusted-paths remove で存在しないパスはエラー"""
        result = configured_cli_runner.run_digest_config("trusted-paths", "remove", "~/nonexistent")
        result.assert_json_status("error")


# =============================================================================
# エラー処理 E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestConfigErrorsE2E:
    """エラー処理のE2Eテスト"""

    def test_no_subcommand_exits_with_error(self, configured_cli_runner: CLIRunner) -> None:
        """サブコマンドなしでエラー"""
        result = configured_cli_runner.run_digest_config()
        result.assert_failure()

    def test_invalid_subcommand_exits_with_error(self, configured_cli_runner: CLIRunner) -> None:
        """無効なサブコマンドでエラー"""
        result = configured_cli_runner.run_digest_config("invalid_command")
        result.assert_failure(2)
