#!/usr/bin/env python3
"""
application/auto_dream/defrag_scanner.py のテスト
==============================================

DefragScanner（件数・threshold 判定 Facade）の検証。
既存 MemoryScanner を再利用し、件数集計と DEFRAG_THRESHOLD 超過判定のみを行う。
剪定候補の検出はしない（Claude の責務）。
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from application.auto_dream.defrag_scanner import DefragScanner
from domain.auto_dream.defrag_types import DEFRAG_THRESHOLD


def _build_memory(base: Path, count: int) -> None:
    """tmp_path 配下に memory dir と count 件の有効 .md（＋MEMORY.md）を構築"""
    memory_dir = base / "C--test" / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("# Memory Index\n", encoding="utf-8")
    for i in range(count):
        (memory_dir / f"entry_{i:03d}.md").write_text(
            f"---\nname: e{i}\ndescription: d{i}\ntype: project\n---\nbody",
            encoding="utf-8",
        )


class TestDefragScannerThreshold:
    """件数集計と閾値判定"""

    @pytest.mark.integration
    def test_メモリなし環境でno_memory(self, tmp_path: Path) -> None:
        """auto-memory 無効環境 → status=no_memory（自動スキップ用）"""
        fake_base = tmp_path / ".claude" / "projects"  # 未作成 → 不在
        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = DefragScanner().scan()
        assert result["status"] == "no_memory"
        assert result["over_threshold"] is False
        assert result["threshold"] == DEFRAG_THRESHOLD

    @pytest.mark.integration
    def test_51件でover_threshold_true(self, tmp_path: Path) -> None:
        """閾値 50 超（51件）→ over_threshold=True"""
        fake_base = tmp_path / ".claude" / "projects"
        _build_memory(fake_base, 51)
        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = DefragScanner().scan()
        assert result["status"] == "ok"
        assert result["file_count"] == 51
        assert result["over_threshold"] is True

    @pytest.mark.integration
    def test_50件ちょうどはover_threshold_false(self, tmp_path: Path) -> None:
        """境界: ちょうど 50 件は超過ではない（条件は > 50）"""
        fake_base = tmp_path / ".claude" / "projects"
        _build_memory(fake_base, 50)
        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = DefragScanner().scan()
        assert result["status"] == "ok"
        assert result["file_count"] == 50
        assert result["over_threshold"] is False


class TestDefragScannerError:
    """例外の防御（MemoryScanner の try/except を継承）"""

    @pytest.mark.integration
    def test_エラー時はerrorステータス(self) -> None:
        """discover が例外 → status=error に包む"""
        with patch(
            "application.auto_dream.memory_scanner.discover_memory_dirs",
            side_effect=RuntimeError("boom"),
        ):
            result = DefragScanner().scan()
        assert result["status"] == "error"
        assert result["error"] is not None
        assert result["threshold"] == DEFRAG_THRESHOLD
