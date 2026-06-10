from __future__ import annotations

import pytest

import adapters.atomic_io as atomic_io
from adapters.state.json_state_store import JsonLeaseStore, JsonOffsetStore
from domain.lease import SessionLease
from domain.offset import UpdateOffset


from tests.conftest import t_utc as _t


def _boom_replace(src, dst):
    raise OSError("simulated crash before publish")


# --- JsonOffsetStore ---


def test_offset_load_returns_initial_when_no_file(tmp_path):
    store = JsonOffsetStore(tmp_path)
    assert store.load().value == 0


def test_offset_save_and_reload_roundtrip(tmp_path):
    store = JsonOffsetStore(tmp_path)
    store.save(UpdateOffset(value=42))
    reloaded = JsonOffsetStore(tmp_path).load()
    assert reloaded.value == 42


def test_offset_corrupted_json_falls_back_to_initial(tmp_path):
    (tmp_path / JsonOffsetStore.FILENAME).write_text("{not json", encoding="utf-8")
    assert JsonOffsetStore(tmp_path).load().value == 0


def test_offset_save_creates_state_dir(tmp_path):
    nested = tmp_path / "sub" / "state"
    store = JsonOffsetStore(nested)
    store.save(UpdateOffset(value=7))
    assert (nested / JsonOffsetStore.FILENAME).exists()


def test_offset_save_failure_preserves_previous_value(tmp_path, monkeypatch):
    """save 途中クラッシュ（publish 前）で旧 offset が無傷＝truncate→write の全損経路がない。"""
    store = JsonOffsetStore(tmp_path)
    store.save(UpdateOffset(value=42))
    monkeypatch.setattr(atomic_io.os, "replace", _boom_replace)
    with pytest.raises(OSError):
        store.save(UpdateOffset(value=43))
    monkeypatch.undo()
    assert JsonOffsetStore(tmp_path).load().value == 42


# --- JsonLeaseStore ---


def test_lease_load_returns_none_when_no_file(tmp_path):
    store = JsonLeaseStore(tmp_path)
    assert store.load() is None


def test_lease_save_and_reload_roundtrip(tmp_path):
    store = JsonLeaseStore(tmp_path)
    lease = SessionLease(owner="session-A", heartbeat=_t(0), ttl_seconds=120)
    store.save(lease)
    reloaded = JsonLeaseStore(tmp_path).load()
    assert reloaded is not None
    assert reloaded.owner == "session-A"
    assert reloaded.heartbeat == _t(0)
    assert reloaded.ttl_seconds == 120


def test_lease_clear_removes_file(tmp_path):
    store = JsonLeaseStore(tmp_path)
    store.save(SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120))
    store.clear()
    assert store.load() is None


def test_lease_clear_is_idempotent_when_no_file(tmp_path):
    store = JsonLeaseStore(tmp_path)
    store.clear()  # no error
    assert store.load() is None


def test_lease_corrupted_json_falls_back_to_none(tmp_path):
    (tmp_path / JsonLeaseStore.FILENAME).write_text("not json at all", encoding="utf-8")
    assert JsonLeaseStore(tmp_path).load() is None


def test_lease_save_failure_preserves_previous_lease(tmp_path, monkeypatch):
    """save 途中クラッシュ（publish 前）で旧 lease が無傷（offset と同型の atomic 保証）。"""
    store = JsonLeaseStore(tmp_path)
    store.save(SessionLease(owner="session-A", heartbeat=_t(0), ttl_seconds=120))
    monkeypatch.setattr(atomic_io.os, "replace", _boom_replace)
    with pytest.raises(OSError):
        store.save(SessionLease(owner="session-B", heartbeat=_t(60), ttl_seconds=120))
    monkeypatch.undo()
    reloaded = JsonLeaseStore(tmp_path).load()
    assert reloaded is not None
    assert reloaded.owner == "session-A"


# --- JsonLeaseStore.try_create（新規取得の排他作成） ---


def test_lease_try_create_succeeds_when_absent(tmp_path):
    """lease ファイル不在時、try_create が True で新規作成する。"""
    store = JsonLeaseStore(tmp_path)
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    assert store.try_create(lease) is True
    reloaded = JsonLeaseStore(tmp_path).load()
    assert reloaded is not None
    assert reloaded.owner == "me"


def test_lease_try_create_returns_false_when_file_exists(tmp_path):
    """既存 lease ファイルがあれば try_create は False で上書きしない（排他作成）。"""
    store = JsonLeaseStore(tmp_path)
    store.save(SessionLease(owner="first", heartbeat=_t(0), ttl_seconds=120))
    second = SessionLease(owner="second", heartbeat=_t(1), ttl_seconds=120)
    assert store.try_create(second) is False
    assert JsonLeaseStore(tmp_path).load().owner == "first"
