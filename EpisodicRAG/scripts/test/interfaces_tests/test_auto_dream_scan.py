#!/usr/bin/env python3
"""
interfaces/auto_dream_scan.py のテスト
=====================================

CLI出力と終了コードのテスト。
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from interfaces.auto_dream_scan import EXIT_ERROR, EXIT_NO_MEMORY, EXIT_OK, main


class TestAutoDreamScanMain:
    """main()関数のテスト"""

    @pytest.mark.integration
    def test_メモリなしで終了コード1(self, tmp_path: Path) -> None:
        """メモリなし → exit code 1"""
        fake_base = tmp_path / ".claude" / "projects"

        with (
            patch(
                "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
                return_value=fake_base,
            ),
            patch("sys.argv", ["auto_dream_scan"]),
        ):
            exit_code = main()

        assert exit_code == EXIT_NO_MEMORY

    @pytest.mark.integration
    def test_正常実行で終了コード0(self, tmp_path: Path) -> None:
        """メモリあり → exit code 0"""
        memory_dir = tmp_path / ".claude" / "projects" / "test" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("# Memory", encoding="utf-8")
        (memory_dir / "test.md").write_text(
            "---\nname: t\ndescription: d\ntype: user\n---\nbody",
            encoding="utf-8",
        )
        fake_base = tmp_path / ".claude" / "projects"

        with (
            patch(
                "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
                return_value=fake_base,
            ),
            patch("sys.argv", ["auto_dream_scan"]),
        ):
            exit_code = main()

        assert exit_code == EXIT_OK

    @pytest.mark.integration
    def test_project_pathオプション(self, tmp_path: Path) -> None:
        """--project-path指定が動作する"""
        memory_dir = tmp_path / ".claude" / "projects" / "C--test" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("# Memory", encoding="utf-8")
        fake_base = tmp_path / ".claude" / "projects"

        with (
            patch(
                "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
                return_value=fake_base,
            ),
            patch("sys.argv", ["auto_dream_scan", "--project-path", "C:\\test"]),
        ):
            exit_code = main()

        assert exit_code == EXIT_OK

    @pytest.mark.integration
    def test_JSON出力がパース可能(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """出力がvalid JSON"""
        fake_base = tmp_path / ".claude" / "projects"

        with (
            patch(
                "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
                return_value=fake_base,
            ),
            patch("sys.argv", ["auto_dream_scan"]),
        ):
            main()

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "status" in parsed
        assert "file_count" in parsed


class TestAutoDreamScanConfigResolution:
    """config.jsonのbase_dirからproject_pathを自動解決するテスト"""

    @pytest.mark.integration
    def test_config_base_dirから正しいプロジェクトを解決(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """複数プロジェクト存在時、configのbase_dirから正しい方を選ぶ"""
        fake_base = tmp_path / ".claude" / "projects"
        # 2つのプロジェクト: 親(C--Users-test) と 子(C--Users-test-DEV)
        for name in ["C--Users-test", "C--Users-test-DEV"]:
            d = fake_base / name / "memory"
            d.mkdir(parents=True)
            (d / "MEMORY.md").write_text("# Memory", encoding="utf-8")

        with (
            patch(
                "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
                return_value=fake_base,
            ),
            # config.base_dir → DEV配下のサブディレクトリを指す
            patch(
                "interfaces.auto_dream_scan.resolve_project_from_config",
                return_value="C:\\Users\\test\\DEV",
            ),
            patch("sys.argv", ["auto_dream_scan"]),
        ):
            exit_code = main()

        assert exit_code == EXIT_OK
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["project_path"] == "C--Users-test-DEV"

    @pytest.mark.integration
    def test_CLI引数がconfigより優先(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--project-path が config を上書きする"""
        fake_base = tmp_path / ".claude" / "projects"
        memory_dir = fake_base / "C--explicit" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("# Memory", encoding="utf-8")

        with (
            patch(
                "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
                return_value=fake_base,
            ),
            # config は別のパスを返すが、CLI引数が勝つ
            patch(
                "interfaces.auto_dream_scan.resolve_project_from_config",
                return_value="C:\\other\\path",
            ),
            patch(
                "sys.argv",
                ["auto_dream_scan", "--project-path", "C:\\explicit"],
            ),
        ):
            exit_code = main()

        assert exit_code == EXIT_OK
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["project_path"] == "C--explicit"

    @pytest.mark.integration
    def test_config未設定時はfallback(self, tmp_path: Path) -> None:
        """config読み込み失敗時はglob-all fallback"""
        fake_base = tmp_path / ".claude" / "projects"
        d = fake_base / "test-project" / "memory"
        d.mkdir(parents=True)
        (d / "MEMORY.md").write_text("# Memory", encoding="utf-8")

        with (
            patch(
                "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
                return_value=fake_base,
            ),
            # config 解決失敗 → None
            patch(
                "interfaces.auto_dream_scan.resolve_project_from_config",
                return_value=None,
            ),
            patch("sys.argv", ["auto_dream_scan"]),
        ):
            exit_code = main()

        # glob-all fallback で1つ見つかる
        assert exit_code == EXIT_OK


class TestAutoDreamScanCLI:
    """subprocess経由のCLIテスト"""

    @pytest.mark.cli
    def test_ヘルプオプション(self) -> None:
        """--help が正常終了"""
        result = subprocess.run(
            [sys.executable, "-m", "interfaces.auto_dream_scan", "--help"],
            capture_output=True,
            cwd=str(Path(__file__).resolve().parents[2]),  # scripts/
            encoding="utf-8",
            errors="replace",
        )
        assert result.returncode == 0
        assert "project-path" in (result.stdout or "")
