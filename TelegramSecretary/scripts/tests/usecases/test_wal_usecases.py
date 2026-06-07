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
from usecases.wal import (
    AppendWalIntent,
    PushWalLog,
    RedoPendingIntents,
    SettleOutboundIntent,
)

from tests.usecases.fakes import (
    FakeGitSync,
    FakeMessageSink,
    FakeRegistryStore,
    FakeWalLogStore,
)


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


# --- RedoPendingIntents: outbound 再送（Stage 3、offset 非依存の at-least-once）---


def _outbound_entry(
    chat_id=100, text="hi", status="pending", created_at="2026-06-03T18:00:00+00:00"
):
    # outbound は registry key を持たないので created_at をキーにする（reconcile 照合に乗らない）
    return WalEntry(
        key=created_at,
        kind="outbound",
        status=status,
        payload={"chat_id": chat_id, "text": text},
        created_at=created_at,
    )


def test_redo_resends_pending_outbound_once_with_apology_prefix():
    sink = FakeMessageSink()
    log = FakeWalLogStore(entries=[_outbound_entry(text="関連トピックあり")])
    result = RedoPendingIntents(log, _services(), sink=sink, now_fn=_now).execute()
    assert len(sink.sent) == 1
    sent = sink.sent[0]
    assert sent.chat_id == 100
    # 元の送信予定時刻＋謝罪プレフィックスが本文頭に付く（鮮度を人間に委ねる＝v4）
    assert "2026-06-03T18:00:00+00:00" in sent.text
    assert "お届けします" in sent.text
    assert "システムが落ちていた" not in sent.text  # 障害断定の除去（偽謝罪の根治）
    assert "関連トピックあり" in sent.text
    assert result["resent"] == 1
    # 再送後 done 化（無限再送防止の起点）
    assert all(e.status == "done" for e in log.load() if e.kind == "outbound")


def test_redo_does_not_resend_outbound_twice():
    sink = FakeMessageSink()
    log = FakeWalLogStore(entries=[_outbound_entry()])
    RedoPendingIntents(log, _services(), sink=sink, now_fn=_now).execute()
    # 1回目で done 化済み。2回目の redo では再送しない（v4 の掃除＝再送→即 done で無限ループ防止）
    result2 = RedoPendingIntents(log, _services(), sink=sink, now_fn=_now).execute()
    assert len(sink.sent) == 1
    assert result2["resent"] == 0


def test_redo_outbound_and_registry_are_independent():
    # 混在 log: registry pending（やり残し）+ outbound pending → 互いに干渉しない
    sink = FakeMessageSink()
    log = FakeWalLogStore(entries=[_entry("T0001"), _outbound_entry()])
    store = FakeRegistryStore(records=[])
    services = {"tasks": RegistryService(store, "id")}
    result = RedoPendingIntents(log, services, sink=sink, now_fn=_now).execute()
    assert {r["id"] for r in store.load()} == {"T0001"}  # registry は upsert
    assert result["redone"] == 1  # registry やり残し（outbound はカウントしない）
    assert result["resent"] == 1  # outbound 再送
    assert len(sink.sent) == 1


def test_redo_without_sink_leaves_outbound_pending():
    # sink 未注入（既存呼び出し）なら outbound は送信されず pending のまま（後方互換）
    log = FakeWalLogStore(entries=[_outbound_entry()])
    result = RedoPendingIntents(log, _services(), now_fn=_now).execute()
    assert result.get("resent", 0) == 0
    assert any(e.status == "pending" and e.kind == "outbound" for e in log.load())


# --- SettleOutboundIntent: 送信成功時の happy-path settle（Stage 2） ---


def test_settle_outbound_intent_marks_sent_done():
    # 送信成功した outbound（key=created_at）を done 化し rewrite する
    log = FakeWalLogStore(entries=[_outbound_entry(created_at="2026-06-03T18:00:00+00:00")])
    SettleOutboundIntent(log).execute("2026-06-03T18:00:00+00:00")
    assert all(e.status == "done" for e in log.load() if e.kind == "outbound")


def test_settle_outbound_intent_only_targets_given_key():
    # 複数 pending のうち指定 key だけ done、他は pending 据え置き
    log = FakeWalLogStore(
        entries=[
            _outbound_entry(created_at="2026-06-03T18:00:00+00:00"),
            _outbound_entry(created_at="2026-06-03T19:00:00+00:00"),
        ]
    )
    SettleOutboundIntent(log).execute("2026-06-03T18:00:00+00:00")
    by = {e.key: e.status for e in log.load()}
    assert by == {
        "2026-06-03T18:00:00+00:00": "done",
        "2026-06-03T19:00:00+00:00": "pending",
    }


def test_settled_outbound_is_not_resent_by_redo():
    # happy-path settle の核心: 送信成功→settle 済みの outbound は次回 redo で再送されない
    # （= 偽謝罪付きの複製が構造的に起きない＝報告①②の根治を直接証明）
    sink = FakeMessageSink()
    log = FakeWalLogStore(entries=[_outbound_entry(created_at="2026-06-03T18:00:00+00:00")])
    SettleOutboundIntent(log).execute("2026-06-03T18:00:00+00:00")
    result = RedoPendingIntents(log, _services(), sink=sink, now_fn=_now).execute()
    assert sink.sent == []
    assert result["resent"] == 0
