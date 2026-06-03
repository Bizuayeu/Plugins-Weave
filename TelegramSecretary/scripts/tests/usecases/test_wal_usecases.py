"""WAL UseCase（AppendWalIntent / PushWalLog / RedoPendingIntents）のテスト。

PushWalLog の must-succeed（best-effort と異なり push 失敗を握らず raise）と、
RedoPendingIntents の upsert→settle→checkpoint（冪等・累積防止）を fake で全分岐検証。
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from domain.exceptions import GitSyncError, PushRejectedError
from domain.wal import WalEntry
from usecases.manage_registry import RegistryService
from usecases.wal import AppendWalIntent, PushWalLog, RedoPendingIntents

from tests.usecases.fakes import FakeGitSync, FakeRegistryStore, FakeWalLogStore


def _now():
    return datetime(2026, 6, 4, 0, 0, 0, tzinfo=timezone.utc)


def _entry(key, status="pending", kind="tasks", created_at="2026-06-03T18:00:00+00:00"):
    return WalEntry(key=key, kind=kind, status=status, payload={"id": key}, created_at=created_at)


def _services(records=None):
    return {"tasks": RegistryService(FakeRegistryStore(records=records or []), "id")}


# --- AppendWalIntent ---

def test_append_writes_pending_entry():
    log = FakeWalLogStore()
    AppendWalIntent(log).execute(
        key="T0001", kind="tasks", payload={"id": "T0001"}, created_at="2026-06-03T18:00:00+00:00"
    )
    assert len(log.append_calls) == 1
    assert log.append_calls[0].status == "pending"
    assert log.append_calls[0].key == "T0001"


# --- PushWalLog: must-succeed（送信前ゲート） ---

def test_push_commits_and_pushes():
    git = FakeGitSync(committed=True, push_outcomes=[None])
    assert PushWalLog(git, Path("WAL.jsonl")).execute("wal: add T0001") is True
    assert git.push_calls == 1


def test_push_noop_when_nothing_committed():
    git = FakeGitSync(committed=False)
    assert PushWalLog(git, Path("WAL.jsonl")).execute("wal: add T0001") is False
    assert git.push_calls == 0


def test_push_non_ff_rebases_then_retries():
    git = FakeGitSync(committed=True, push_outcomes=[PushRejectedError("non-ff"), None])
    assert PushWalLog(git, Path("WAL.jsonl")).execute("wal: add T0001") is True
    assert git.pull_rebase_calls == 1
    assert git.push_calls == 2


def test_push_raises_when_retry_still_rejected():
    git = FakeGitSync(committed=True, push_outcomes=[PushRejectedError("r1"), PushRejectedError("r2")])
    with pytest.raises(PushRejectedError):
        PushWalLog(git, Path("WAL.jsonl")).execute("wal: add T0001")


def test_push_raises_on_network_error_not_swallowed():
    # best-effort の RegistrySyncService と異なり、GitSyncError を握らず伝播（送信前ゲートの要）
    git = FakeGitSync(committed=True, push_outcomes=[GitSyncError("network down")])
    with pytest.raises(GitSyncError):
        PushWalLog(git, Path("WAL.jsonl")).execute("wal: add T0001")


# --- RedoPendingIntents ---

def test_redo_upserts_missing_and_marks_all_done():
    log = FakeWalLogStore(entries=[_entry("T0001"), _entry("T0002")])
    store = FakeRegistryStore(records=[{"id": "T0001"}])  # T0001 は既に registry にある
    services = {"tasks": RegistryService(store, "id")}
    result = RedoPendingIntents(log, services, now_fn=_now).execute()
    # やり残し T0002 が registry に upsert される
    assert {r["id"] for r in store.load()} == {"T0001", "T0002"}
    assert result["redone"] == 1
    # ログの全 entry が done 化（T0001 既反映 + T0002 今 upsert）
    assert all(e.status == "done" for e in log.load())


def test_redo_is_idempotent():
    log = FakeWalLogStore(entries=[_entry("T0001")])
    store = FakeRegistryStore(records=[])
    services = {"tasks": RegistryService(store, "id")}
    RedoPendingIntents(log, services, now_fn=_now).execute()
    result2 = RedoPendingIntents(log, services, now_fn=_now).execute()
    # 二度目: T0001 は既に registry にあるので reconcile が空＝upsert しない
    assert result2["redone"] == 0
    assert len([r for r in store.load() if r["id"] == "T0001"]) == 1  # 重複なし


def test_redo_checkpoint_drops_old_done():
    # done 化された古い entry は checkpoint で掃除される（pending 累積防止の出口）
    old_done = _entry("T0001", status="done", created_at="2026-06-01T00:00:00+00:00")  # 3日前
    log = FakeWalLogStore(entries=[old_done])
    result = RedoPendingIntents(log, _services(), now_fn=_now, retention_h=24).execute()
    assert log.load() == []  # 古い done は掃除
    assert result["kept"] == 0
