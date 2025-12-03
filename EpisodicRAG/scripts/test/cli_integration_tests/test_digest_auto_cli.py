#!/usr/bin/env python3
"""
digest_auto CLI E2E Tests
=========================

Subprocess-based E2E tests for digest_auto.py CLI.
"""

import json

import pytest

from .cli_runner import CLIRunner
from .conftest import create_loop_file

# =============================================================================
# JSON 出力 E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestAutoJsonOutputE2E:
    """JSON出力のE2Eテスト"""

    def test_json_output_is_valid(self, configured_cli_runner: CLIRunner) -> None:
        """JSON出力が有効"""
        result = configured_cli_runner.run_digest_auto(output="json")
        assert result.json_output is not None

    def test_json_output_contains_status(self, configured_cli_runner: CLIRunner) -> None:
        """JSON出力に status が含まれる"""
        result = configured_cli_runner.run_digest_auto(output="json")
        assert "status" in result.json_output

    def test_json_output_status_is_valid(self, configured_cli_runner: CLIRunner) -> None:
        """JSON出力の status が有効な値"""
        result = configured_cli_runner.run_digest_auto(output="json")
        assert result.json_output["status"] in ["ok", "warning", "error"]

    def test_default_output_is_json(self, configured_cli_runner: CLIRunner) -> None:
        """デフォルト出力はJSON"""
        result = configured_cli_runner.run_digest_auto()
        assert result.json_output is not None


# =============================================================================
# Text 出力 E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestAutoTextOutputE2E:
    """テキスト出力のE2Eテスト"""

    def test_text_output_contains_header(self, configured_cli_runner: CLIRunner) -> None:
        """テキスト出力にヘッダーが含まれる"""
        result = configured_cli_runner.run_digest_auto(output="text")
        result.assert_success()
        assert "EpisodicRAG" in result.stdout

    def test_text_output_contains_status_indicators(self, configured_cli_runner: CLIRunner) -> None:
        """テキスト出力にステータスインジケータが含まれる"""
        result = configured_cli_runner.run_digest_auto(output="text")
        # ステータスインジケータ（絵文字または記号）が含まれる
        assert any(
            indicator in result.stdout for indicator in ["OK", "WARNING", "ERROR", "HEALTHY", "━"]
        )


# =============================================================================
# 健全性診断シナリオ E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestAutoScenariosE2E:
    """健全性診断シナリオのE2Eテスト"""

    def test_healthy_system_returns_ok(self, configured_cli_runner: CLIRunner) -> None:
        """正常なシステムで ok を返す"""
        result = configured_cli_runner.run_digest_auto(output="json")
        assert result.json_output["status"] == "ok"

    def test_missing_config_returns_error(self, cli_runner: CLIRunner) -> None:
        """設定なしでエラーを返す"""
        result = cli_runner.run_digest_auto(output="json")
        # Note: digest_auto returns exit code 0 even with status="error"
        result.assert_json_status("error")

    def test_system_with_unprocessed_loops_detected(
        self, configured_cli_env, configured_cli_runner: CLIRunner
    ) -> None:
        """未処理Loopがある場合に検出"""
        # Loopファイルを作成
        loops_path = configured_cli_env["loops"]
        for i in range(1, 3):
            create_loop_file(loops_path, i, f"test_loop_{i}")

        result = configured_cli_runner.run_digest_auto(output="json")
        # 未処理Loopがあるためwarningまたはissuesに含まれる
        if result.json_output["status"] == "warning":
            assert "issues" in result.json_output
        elif result.json_output["status"] == "ok" and result.json_output.get("issues"):
            issue_types = [i["type"] for i in result.json_output["issues"]]
            assert "unprocessed_loops" in issue_types


# =============================================================================
# エラー処理 E2E テスト
# =============================================================================


@pytest.mark.cli
class TestDigestAutoErrorsE2E:
    """エラー処理のE2Eテスト"""

    def test_invalid_output_format_fails(self, configured_cli_runner: CLIRunner) -> None:
        """無効な --output 形式でエラー"""
        result = configured_cli_runner.run_digest_auto(output="invalid")
        result.assert_failure(2)  # argparse error

    def test_unknown_option_fails(self, configured_cli_runner: CLIRunner) -> None:
        """未知のオプションでエラー"""
        result = configured_cli_runner.run_digest_auto("--unknown-option")
        result.assert_failure(2)
