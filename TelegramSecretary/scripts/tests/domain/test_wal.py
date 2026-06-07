"""WAL Domain（WalEntry / reconcile / settle / checkpoint）の純関数テスト。

reconcile（やり残し抽出）と settle（done 化）が全 pending を漏れなく二分すること、
checkpoint が pending を無条件保持しつつ done を retention で掃除することを駆動する。
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.wal import WalEntry, checkpoint, reconcile, settle, settle_outbound


def _entry(key, status="pending", kind="tasks", created_at="2026-06-03T00:00:00+00:00"):
    return WalEntry(key=key, kind=kind, status=status, payload={"id": key}, created_at=created_at)


# --- WalEntry: from_dict/to_dict と enum 検証（registry.py と同型） ---

def test_walentry_roundtrip():
    e = _entry("T0001")
    assert WalEntry.from_dict(e.to_dict()) == e


def test_walentry_rejects_unknown_status():
    with pytest.raises(ValueError):
        WalEntry(key="T0001", kind="tasks", status="weird", payload={}, created_at="2026-06-03T00:00:00+00:00")


def test_walentry_from_dict_rejects_unknown_status():
    with pytest.raises(ValueError):
        WalEntry.from_dict(
            {"key": "T0001", "kind": "tasks", "status": "weird", "payload": {}, "created_at": "2026-06-03T00:00:00+00:00"}
        )


# --- reconcile: pending ∖ registry_keys（やり残し抽出） ---

def test_reconcile_returns_pending_not_in_registry():
    entries = [_entry("T0001"), _entry("T0002"), _entry("T0003")]
    registry_keys = {("tasks", "T0001")}
    assert [e.key for e in reconcile(entries, registry_keys)] == ["T0002", "T0003"]


def test_reconcile_excludes_done():
    entries = [_entry("T0001", status="done"), _entry("T0002")]
    assert [e.key for e in reconcile(entries, set())] == ["T0002"]


def test_reconcile_empty_when_all_in_registry():
    entries = [_entry("T0001"), _entry("T0002")]
    registry_keys = {("tasks", "T0001"), ("tasks", "T0002")}
    assert reconcile(entries, registry_keys) == []


def test_reconcile_is_kind_aware():
    # 同じ key でも kind が違えば別物（tasks T0001 と individuals T0001）
    entries = [_entry("X1", kind="tasks"), _entry("X1", kind="individuals")]
    registry_keys = {("tasks", "X1")}
    assert [(e.kind, e.key) for e in reconcile(entries, registry_keys)] == [("individuals", "X1")]


# --- settle: registry に key がある pending を done 化 ---

def test_settle_marks_pending_in_registry_as_done():
    entries = [_entry("T0001"), _entry("T0002"), _entry("T0003")]
    registry_keys = {("tasks", "T0001"), ("tasks", "T0002")}
    by_key = {e.key: e.status for e in settle(entries, registry_keys)}
    assert by_key == {"T0001": "done", "T0002": "done", "T0003": "pending"}


def test_settle_leaves_existing_done_untouched():
    entries = [_entry("T0001", status="done")]
    out = settle(entries, {("tasks", "T0001")})
    assert out[0].status == "done"


def test_reconcile_and_settle_partition_all_pending():
    # reconcile（やり残し）と settle が done 化する集合は、全 pending を漏れ・重複なく二分する
    entries = [_entry("T0001"), _entry("T0002"), _entry("T0003")]
    registry_keys = {("tasks", "T0001")}
    todo_keys = {e.key for e in reconcile(entries, registry_keys)}
    done_keys = {e.key for e in settle(entries, registry_keys) if e.status == "done"}
    pending_keys = {e.key for e in entries if e.status == "pending"}
    assert todo_keys | done_keys == pending_keys
    assert todo_keys & done_keys == set()


# --- checkpoint: pending 無条件保持、done を retention で掃除 ---

def test_checkpoint_keeps_pending_regardless_of_age():
    now = datetime(2026, 6, 4, 0, 0, 0, tzinfo=timezone.utc)
    old_pending = _entry("T0001", status="pending", created_at="2026-01-01T00:00:00+00:00")
    assert len(checkpoint([old_pending], now, retention_h=24)) == 1


def test_checkpoint_drops_done_older_than_retention():
    now = datetime(2026, 6, 4, 0, 0, 0, tzinfo=timezone.utc)
    old_done = _entry("T0001", status="done", created_at="2026-06-02T00:00:00+00:00")  # 2日前
    fresh_done = _entry("T0002", status="done", created_at="2026-06-03T18:00:00+00:00")  # 6h前
    out = checkpoint([old_done, fresh_done], now, retention_h=24)
    assert [e.key for e in out] == ["T0002"]


# --- settle_outbound: 指定 key の outbound pending を done 化（happy-path settle） ---

def test_settle_outbound_marks_matching_pending_done():
    # 送信成功した本人が key 直指定で done 化（外部真実源の無い outbound の冪等化）
    entries = [_entry("k1", kind="outbound"), _entry("k2", kind="outbound")]
    by_key = {e.key: e.status for e in settle_outbound(entries, "k1")}
    assert by_key == {"k1": "done", "k2": "pending"}


def test_settle_outbound_ignores_non_outbound_same_key():
    # 同じ key でも registry kind は触らない（kind=outbound 限定＝reconcile/settle 経路を侵さない）
    entries = [_entry("k1", kind="tasks"), _entry("k1", kind="outbound")]
    by = {(e.kind, e.key): e.status for e in settle_outbound(entries, "k1")}
    assert by == {("tasks", "k1"): "pending", ("outbound", "k1"): "done"}


def test_settle_outbound_leaves_existing_done_untouched():
    entries = [_entry("k1", status="done", kind="outbound")]
    assert settle_outbound(entries, "k1")[0].status == "done"


def test_settle_outbound_noop_when_key_absent():
    # 該当 key が無ければ全件不変（送信前クラッシュで append すら無い場合の安全）
    entries = [_entry("k1", kind="outbound"), _entry("k2", kind="outbound")]
    assert [e.status for e in settle_outbound(entries, "zzz")] == ["pending", "pending"]


def test_settle_outbound_preserves_order():
    entries = [_entry("a", kind="outbound"), _entry("b", kind="tasks"), _entry("c", kind="outbound")]
    out = settle_outbound(entries, "c")
    assert [e.key for e in out] == ["a", "b", "c"]
    assert [e.status for e in out] == ["pending", "pending", "done"]
