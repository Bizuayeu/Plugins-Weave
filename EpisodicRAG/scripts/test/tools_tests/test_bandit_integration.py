#!/usr/bin/env python3
"""
test_bandit_integration.py
==========================

Bandit セキュリティスキャン統合テスト。
TDDで開発: Red → Green → Refactor

セキュリティツールの統合確認:
- Banditが実行可能か
- 設定ファイルが存在するか
- HIGH severity の問題がないか
"""

import subprocess
from pathlib import Path

import pytest

# scriptsディレクトリのパス
SCRIPTS_DIR = Path(__file__).parent.parent.parent


# =============================================================================
# Cycle 1: Bandit 実行可能性テスト
# =============================================================================


class TestBanditExecution:
    """Bandit 実行の基本テスト"""

    @pytest.mark.cli
    def test_bandit_is_installed(self) -> None:
        """Banditがインストールされている"""
        result = subprocess.run(
            ["python", "-m", "bandit", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "Bandit is not installed"
        # バージョン出力には "1.9" などのバージョン番号が含まれる
        assert "1." in result.stdout, f"Unexpected version output: {result.stdout}"

    @pytest.mark.cli
    def test_bandit_runs_on_scripts_directory(self) -> None:
        """Banditがscriptsディレクトリで実行可能"""
        result = subprocess.run(
            [
                "python",
                "-m",
                "bandit",
                "-r",
                str(SCRIPTS_DIR),
                "--exclude",
                "test",
                "--severity-level",
                "medium",
            ],
            capture_output=True,
            text=True,
        )
        # 0 = no issues, 1 = issues found (どちらも実行成功)
        assert result.returncode in (0, 1), f"Bandit failed: {result.stderr}"


# =============================================================================
# Cycle 2: 設定ファイル存在テスト
# =============================================================================


class TestBanditConfiguration:
    """Bandit 設定ファイルのテスト"""

    @pytest.mark.cli
    def test_bandit_config_file_exists(self) -> None:
        """設定ファイル .bandit が存在する"""
        config_path = SCRIPTS_DIR.parent / ".bandit"
        assert config_path.exists(), f".bandit 設定ファイルが必要: {config_path}"

    @pytest.mark.cli
    def test_bandit_runs_with_config_file(self) -> None:
        """設定ファイルを使用してBanditが実行可能"""
        config_path = SCRIPTS_DIR.parent / ".bandit"
        if not config_path.exists():
            pytest.skip(".bandit config file not found")

        result = subprocess.run(
            [
                "python",
                "-m",
                "bandit",
                "-r",
                str(SCRIPTS_DIR),
                f"--configfile={config_path}",
                "--severity-level",
                "medium",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode in (0, 1), f"Bandit with config failed: {result.stderr}"


# =============================================================================
# Cycle 3: セキュリティ品質テスト
# =============================================================================


class TestSecurityQuality:
    """セキュリティ品質の検証"""

    @pytest.mark.cli
    def test_no_high_severity_issues(self) -> None:
        """HIGH severity の問題がない"""
        result = subprocess.run(
            [
                "python",
                "-m",
                "bandit",
                "-r",
                str(SCRIPTS_DIR),
                "--exclude",
                "test",
                "--severity-level",
                "high",
                "-f",
                "json",
            ],
            capture_output=True,
            text=True,
        )
        # returncode 0 = no issues found
        assert result.returncode == 0, f"HIGH severity security issues detected:\n{result.stdout}"

    @pytest.mark.cli
    def test_no_medium_severity_issues_in_production_code(self) -> None:
        """本番コード (domain, application, infrastructure, interfaces) に MEDIUM 問題がない"""
        production_dirs = ["domain", "application", "infrastructure", "interfaces"]

        for dir_name in production_dirs:
            dir_path = SCRIPTS_DIR / dir_name
            if not dir_path.exists():
                continue

            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "bandit",
                    "-r",
                    str(dir_path),
                    "--severity-level",
                    "medium",
                    "-f",
                    "json",
                ],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"MEDIUM severity issues in {dir_name}:\n{result.stdout}"
