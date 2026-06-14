#!/usr/bin/env python3
"""
infrastructure/auto_dream/snapshot_writer.py のテスト
===================================================

剪定前スナップショット（revert 不能対策）の検証。
auto-memory は git 非追跡のため、これが唯一の復元手段。
"""

from pathlib import Path

import pytest

from infrastructure.auto_dream.snapshot_writer import create_snapshot


def _build_memory(base: Path) -> Path:
    """memory dir（MEMORY.md + 2 entries）を構築して返す"""
    memory_dir = base / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text("# Memory Index\n", encoding="utf-8")
    (memory_dir / "a.md").write_text(
        "---\nname: a\ndescription: d\ntype: user\n---\nx", encoding="utf-8"
    )
    (memory_dir / "b.md").write_text(
        "---\nname: b\ndescription: d\ntype: project\n---\ny", encoding="utf-8"
    )
    return memory_dir


class TestCreateSnapshot:
    """create_snapshot の検証"""

    @pytest.mark.integration
    def test_スナップショットが全ファイルを複製(self, tmp_path: Path) -> None:
        """MEMORY.md と全 *.md がコピー先に存在する"""
        memory_dir = _build_memory(tmp_path / "src")
        snap_root = tmp_path / "snaps"

        dest = create_snapshot(memory_dir, snapshot_root=snap_root)

        assert dest.exists()
        assert (dest / "MEMORY.md").exists()
        assert (dest / "a.md").exists()
        assert (dest / "b.md").exists()

    @pytest.mark.integration
    def test_格納先は走査対象dirの外(self, tmp_path: Path) -> None:
        """snapshot は memory dir の内側・兄弟ではなく snapshot_root 配下に作る"""
        memory_dir = _build_memory(tmp_path / "src")
        snap_root = tmp_path / "snaps"

        dest = create_snapshot(memory_dir, snapshot_root=snap_root)

        assert snap_root in dest.parents
        assert memory_dir not in dest.parents  # memory dir 内に作らない

    @pytest.mark.integration
    def test_同一timestampでも衝突せず別パス(self, tmp_path: Path) -> None:
        """同一 timestamp での二度の snapshot が別パスになる（上書き回避）"""
        memory_dir = _build_memory(tmp_path / "src")
        snap_root = tmp_path / "snaps"

        first = create_snapshot(memory_dir, snapshot_root=snap_root, timestamp="20260614T000000Z")
        second = create_snapshot(memory_dir, snapshot_root=snap_root, timestamp="20260614T000000Z")

        assert first != second
        assert first.exists() and second.exists()
        assert "20260614T000000Z" in first.name

    @pytest.mark.integration
    def test_存在しないdirで例外(self, tmp_path: Path) -> None:
        """対象 memory dir が無ければ FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            create_snapshot(tmp_path / "nope", snapshot_root=tmp_path / "snaps")
