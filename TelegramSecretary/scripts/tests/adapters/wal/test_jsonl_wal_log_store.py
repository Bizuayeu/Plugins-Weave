"""JsonlWalLogStore（WAL ログの JSONL 永続化）のテスト。実ファイル I/O は tmp_path。"""
from __future__ import annotations

import json

import pytest

from domain.wal import WalEntry

import adapters.atomic_io as atomic_io
from adapters.wal.jsonl_wal_log_store import JsonlWalLogStore


def _entry(key, status="pending"):
    return WalEntry(
        key=key, kind="tasks", status=status, payload={"id": key},
        created_at="2026-06-03T18:00:00+00:00",
    )


def test_append_then_load_roundtrip(tmp_path):
    store = JsonlWalLogStore(tmp_path / "wal" / "WAL.jsonl")  # 親ディレクトリ自動作成
    store.append(_entry("T0001"))
    store.append(_entry("T0002"))
    loaded = store.load()
    assert [e.key for e in loaded] == ["T0001", "T0002"]  # 順序保持
    assert loaded[0].payload == {"id": "T0001"}


def test_load_missing_file_returns_empty(tmp_path):
    assert JsonlWalLogStore(tmp_path / "WAL.jsonl").load() == []


def test_load_skips_corrupt_lines(tmp_path):
    path = tmp_path / "WAL.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_entry("T0001").to_dict(), ensure_ascii=False) + "\n"
        + "{ broken json line\n"
        + json.dumps(_entry("T0002").to_dict(), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    loaded = JsonlWalLogStore(path).load()
    assert [e.key for e in loaded] == ["T0001", "T0002"]  # 破損行を飛ばし両端を読む


def test_rewrite_replaces_all(tmp_path):
    store = JsonlWalLogStore(tmp_path / "WAL.jsonl")
    store.append(_entry("T0001"))
    store.append(_entry("T0002"))
    store.rewrite([_entry("T0002", status="done")])  # checkpoint 後を想定
    loaded = store.load()
    assert [e.key for e in loaded] == ["T0002"]
    assert loaded[0].status == "done"


def test_rewrite_failure_preserves_previous_entries(tmp_path, monkeypatch):
    """rewrite 途中クラッシュ（publish 前）で旧 WAL が無傷。

    WAL は must-succeed 装置——checkpoint の全書換中に死んで全損するのは自己矛盾。
    """
    store = JsonlWalLogStore(tmp_path / "WAL.jsonl")
    store.append(_entry("T0001"))
    store.append(_entry("T0002"))

    def boom(src, dst):
        raise OSError("simulated crash before publish")

    monkeypatch.setattr(atomic_io.os, "replace", boom)
    with pytest.raises(OSError):
        store.rewrite([_entry("T0002", status="done")])
    monkeypatch.undo()
    assert [e.key for e in store.load()] == ["T0001", "T0002"]


def test_append_preserves_japanese(tmp_path):
    store = JsonlWalLogStore(tmp_path / "WAL.jsonl")
    store.append(
        WalEntry(
            key="T0001", kind="tasks", status="pending",
            payload={"title": "プレスリリース発表"}, created_at="2026-06-03T18:00:00+00:00",
        )
    )
    assert store.load()[0].payload["title"] == "プレスリリース発表"  # ensure_ascii=False
