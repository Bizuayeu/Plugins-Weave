#!/usr/bin/env python3
"""
interfaces/dream_defrag.py のテスト
=================================

dream-defrag CLI（scan / snapshot / rebuild-index）の出力・終了コード検証。
CLI は決定論操作のみを露出する（剪定の意思決定 API は持たない）。
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from interfaces.dream_defrag import EXIT_NO_MEMORY, EXIT_OK, main

_GCPB = "infrastructure.auto_dream.memory_discovery.get_claude_projects_base"


def _build_memory(base: Path, count: int = 2) -> Path:
    """fake base 配下に memory dir（index は未存在 p.md を参照）を構築"""
    memory_dir = base / "C--test" / "memory"
    memory_dir.mkdir(parents=True)
    # index は p.md を参照するが、ディスクには置かない（rebuild の剪定対象）
    (memory_dir / "MEMORY.md").write_text(
        "# Memory Index\n\n## User\n- [プロファイル](p.md) — 認知特性\n",
        encoding="utf-8",
    )
    for i in range(count):
        (memory_dir / f"e{i}.md").write_text(
            f"---\nname: n{i}\ndescription: d{i}\ntype: project\n---\nbody",
            encoding="utf-8",
        )
    return memory_dir


class TestScanSubcommand:
    @pytest.mark.integration
    def test_scanでJSON出力がパース可能(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_base = tmp_path / ".claude" / "projects"
        _build_memory(fake_base)
        with patch(_GCPB, return_value=fake_base), patch("sys.argv", ["dream_defrag", "scan"]):
            main()
        parsed = json.loads(capsys.readouterr().out)
        assert "status" in parsed
        assert "file_count" in parsed
        assert "over_threshold" in parsed

    @pytest.mark.integration
    def test_メモリなしで終了コード1(self, tmp_path: Path) -> None:
        fake_base = tmp_path / ".claude" / "projects"  # 未作成
        with patch(_GCPB, return_value=fake_base), patch("sys.argv", ["dream_defrag", "scan"]):
            assert main() == EXIT_NO_MEMORY


class TestSnapshotSubcommand:
    @pytest.mark.integration
    def test_snapshotがパスを返す(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        fake_base = tmp_path / ".claude" / "projects"
        _build_memory(fake_base)
        with (
            patch(_GCPB, return_value=fake_base),
            patch(
                "infrastructure.auto_dream.snapshot_writer.default_snapshot_root",
                return_value=tmp_path / "snaps",
            ),
            patch("sys.argv", ["dream_defrag", "snapshot"]),
        ):
            code = main()
        parsed = json.loads(capsys.readouterr().out)
        assert code == EXIT_OK
        assert parsed["status"] == "ok"
        assert parsed["snapshot_path"]
        assert Path(parsed["snapshot_path"]).exists()


class TestRebuildIndexSubcommand:
    @pytest.mark.integration
    def test_previewは書き込まず候補を返す(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_base = tmp_path / ".claude" / "projects"
        memory_dir = _build_memory(fake_base)
        before = (memory_dir / "MEMORY.md").read_text(encoding="utf-8")
        with (
            patch(_GCPB, return_value=fake_base),
            patch("sys.argv", ["dream_defrag", "rebuild-index", "--preview"]),
        ):
            code = main()
        parsed = json.loads(capsys.readouterr().out)
        assert code == EXIT_OK
        assert parsed["preview"] is True
        assert "p.md" not in parsed["index_text"]  # 未存在エントリは落ちる
        # プレビューはディスクを変更しない
        assert (memory_dir / "MEMORY.md").read_text(encoding="utf-8") == before

    @pytest.mark.integration
    def test_applyで書き込む(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        fake_base = tmp_path / ".claude" / "projects"
        memory_dir = _build_memory(fake_base)
        with (
            patch(_GCPB, return_value=fake_base),
            patch("sys.argv", ["dream_defrag", "rebuild-index"]),
        ):
            code = main()
        parsed = json.loads(capsys.readouterr().out)
        assert code == EXIT_OK
        assert parsed["preview"] is False
        # 未存在エントリ p.md が索引から消えている
        assert "p.md" not in (memory_dir / "MEMORY.md").read_text(encoding="utf-8")


class TestCLI:
    @pytest.mark.cli
    def test_ヘルプオプション(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "interfaces.dream_defrag", "--help"],
            capture_output=True,
            cwd=str(Path(__file__).resolve().parents[2]),  # scripts/
            encoding="utf-8",
            errors="replace",
        )
        assert result.returncode == 0
        assert "scan" in (result.stdout or "")
