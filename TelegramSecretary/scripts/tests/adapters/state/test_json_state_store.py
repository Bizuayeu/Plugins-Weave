from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adapters.state.json_state_store import JsonLeaseStore, JsonOffsetStore
from domain.lease import SessionLease
from domain.offset import UpdateOffset


def _t(seconds: int = 0) -> datetime:
    base = datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=seconds)


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
