from __future__ import annotations

import os
import time
from pathlib import Path

from infrastructure.media_cleanup import cleanup_media_dir


def test_cleanup_returns_zero_when_dir_missing(tmp_path: Path):
    assert cleanup_media_dir(tmp_path / "nonexistent", retention_seconds=3600) == 0


def test_cleanup_deletes_files_older_than_retention(tmp_path: Path):
    target_dir = tmp_path / "media"
    target_dir.mkdir()
    old = target_dir / "old.jpg"
    fresh = target_dir / "fresh.jpg"
    old.write_bytes(b"a")
    fresh.write_bytes(b"b")
    # old は 2h 前に書かれた扱い
    two_hours_ago = time.time() - 2 * 3600
    os.utime(old, (two_hours_ago, two_hours_ago))

    # retention=1h → old は削除、fresh は残る
    removed = cleanup_media_dir(target_dir, retention_seconds=3600)
    assert removed == 1
    assert not old.exists()
    assert fresh.exists()


def test_cleanup_keeps_files_within_retention(tmp_path: Path):
    target_dir = tmp_path / "media"
    target_dir.mkdir()
    file_a = target_dir / "recent.jpg"
    file_a.write_bytes(b"a")
    # default mtime (now) のまま、retention=1h → 削除されない
    removed = cleanup_media_dir(target_dir, retention_seconds=3600)
    assert removed == 0
    assert file_a.exists()


def test_cleanup_ignores_subdirectories(tmp_path: Path):
    """サブディレクトリは触らない（フラット保存前提）。"""
    target_dir = tmp_path / "media"
    target_dir.mkdir()
    sub = target_dir / "sub"
    sub.mkdir()
    old_file = target_dir / "old.jpg"
    old_file.write_bytes(b"a")
    os.utime(old_file, (0, 0))

    removed = cleanup_media_dir(target_dir, retention_seconds=3600)
    assert removed == 1
    assert sub.exists()  # ディレクトリは残る


def test_cleanup_uses_injected_now(tmp_path: Path):
    """now を注入できるので fake clock テスト可能。"""
    target_dir = tmp_path / "media"
    target_dir.mkdir()
    file_a = target_dir / "a.jpg"
    file_a.write_bytes(b"a")
    mtime = file_a.stat().st_mtime
    # now を mtime+10秒で固定、retention=5 → 削除対象
    removed = cleanup_media_dir(target_dir, retention_seconds=5, now=mtime + 10)
    assert removed == 1


def test_cleanup_does_not_die_on_oserror(tmp_path: Path, monkeypatch):
    """個別ファイルの削除失敗で処理が止まらない（best-effort）。"""
    target_dir = tmp_path / "media"
    target_dir.mkdir()
    file_a = target_dir / "a.jpg"
    file_b = target_dir / "b.jpg"
    file_a.write_bytes(b"a")
    file_b.write_bytes(b"b")
    old_mtime = time.time() - 7200
    os.utime(file_a, (old_mtime, old_mtime))
    os.utime(file_b, (old_mtime, old_mtime))

    original_unlink = Path.unlink
    call_count = {"n": 0}

    def fail_first_unlink(self, missing_ok=False):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise OSError("simulated permission error")
        return original_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", fail_first_unlink)

    # 1つ目で OSError、2つ目は成功して 1 を返す
    removed = cleanup_media_dir(target_dir, retention_seconds=3600)
    assert removed == 1
