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
from tests.usecases.fakes import (
    FakeGitSync,
    FakeMessageSink,
    FakeRegistryStore,
    FakeWalLogStore,
)
from usecases.manage_registry import RegistryService
from usecases.wal import (
    AppendWalIntent,
    DropDeadIntent,
    PushWalLog,
    RedoPendingIntents,
    SettleOutboundIntent,
)


def _now():
    return datetime(2026, 6, 4, 0, 0, 0, tzinfo=timezone.utc)


def _entry(key, status="pending", kind="tasks", created_at="2026-06-03T18:00:00+00:00"):
    return WalEntry(
        key=key, kind=kind, status=status, payload={"id": key}, created_at=created_at
    )


def _services(records=None):
    return {"tasks": RegistryService(FakeRegistryStore(records=records or []), "id")}


def _identity(kind, payload):
    """素通しの validate（`lambda kind, p: p` の共有版）。

    `validate` は必須引数なので、検証を主題にしないテストは全てこれを渡す
    （省略可にすると注入し忘れが素通りする穴が UseCase 内に再生する）。
    """
    return payload


# --- AppendWalIntent ---


def test_append_writes_pending_entry():
    log = FakeWalLogStore()
    AppendWalIntent(log).execute(
        key="T0001",
        kind="tasks",
        payload={"id": "T0001"},
        created_at="2026-06-03T18:00:00+00:00",
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
    git = FakeGitSync(
        committed=True, push_outcomes=[PushRejectedError("r1"), PushRejectedError("r2")]
    )
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
    result = RedoPendingIntents(log, services, _identity, now_fn=_now).execute()
    # やり残し T0002 が registry に upsert される
    assert {r["id"] for r in store.load()} == {"T0001", "T0002"}
    assert result["redone"] == 1
    # ログの全 entry が done 化（T0001 既反映 + T0002 今 upsert）
    assert all(e.status == "done" for e in log.load())


def test_redo_is_idempotent():
    log = FakeWalLogStore(entries=[_entry("T0001")])
    store = FakeRegistryStore(records=[])
    services = {"tasks": RegistryService(store, "id")}
    RedoPendingIntents(log, services, _identity, now_fn=_now).execute()
    result2 = RedoPendingIntents(log, services, _identity, now_fn=_now).execute()
    # 二度目: T0001 は既に registry にあるので reconcile が空＝upsert しない
    assert result2["redone"] == 0
    assert len([r for r in store.load() if r["id"] == "T0001"]) == 1  # 重複なし


def test_redo_checkpoint_drops_old_done():
    # done 化された古い entry は checkpoint で掃除される（pending 累積防止の出口）
    old_done = _entry(
        "T0001", status="done", created_at="2026-06-01T00:00:00+00:00"
    )  # 3日前
    log = FakeWalLogStore(entries=[old_done])
    result = RedoPendingIntents(
        log, _services(), _identity, now_fn=_now, retention_h=24
    ).execute()
    assert log.load() == []  # 古い done は掃除
    assert result["kept"] == 0


# --- RedoPendingIntents: outbound 再送（offset 非依存の at-least-once）---


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
    result = RedoPendingIntents(
        log, _services(), _identity, sink=sink, now_fn=_now
    ).execute()
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
    RedoPendingIntents(log, _services(), _identity, sink=sink, now_fn=_now).execute()
    # 1回目で done 化済み。2回目の redo では再送しない（v4 の掃除＝再送→即 done で無限ループ防止）
    result2 = RedoPendingIntents(
        log, _services(), _identity, sink=sink, now_fn=_now
    ).execute()
    assert len(sink.sent) == 1
    assert result2["resent"] == 0


def test_redo_outbound_and_registry_are_independent():
    # 混在 log: registry pending（やり残し）+ outbound pending → 互いに干渉しない
    sink = FakeMessageSink()
    log = FakeWalLogStore(entries=[_entry("T0001"), _outbound_entry()])
    store = FakeRegistryStore(records=[])
    services = {"tasks": RegistryService(store, "id")}
    result = RedoPendingIntents(
        log, services, _identity, sink=sink, now_fn=_now
    ).execute()
    assert {r["id"] for r in store.load()} == {"T0001"}  # registry は upsert
    assert result["redone"] == 1  # registry やり残し（outbound はカウントしない）
    assert result["resent"] == 1  # outbound 再送
    assert len(sink.sent) == 1


def test_redo_preserves_interleaved_order_of_registry_and_outbound():
    """checkpoint 後も WAL の時系列（registry / outbound の interleave 順）が保たれる。

    WAL は整合性と短期記憶（直近 retention の会話文脈）の二役を担うため、
    kind 別分離→連結で読み出し順が崩れてはならない（R-34）。
    """
    sink = FakeMessageSink()
    log = FakeWalLogStore(
        entries=[
            _entry("T0001", created_at="2026-06-03T18:00:00+00:00"),
            _outbound_entry(created_at="2026-06-03T19:00:00+00:00"),
            _entry("T0002", created_at="2026-06-03T20:00:00+00:00"),
            _outbound_entry(created_at="2026-06-03T21:00:00+00:00"),
        ]
    )
    store = FakeRegistryStore(records=[])
    services = {"tasks": RegistryService(store, "id")}
    RedoPendingIntents(log, services, _identity, sink=sink, now_fn=_now).execute()
    # 全 entry が retention 内 done で残り、元の interleave 順をそのまま保持する
    assert [(e.kind, e.created_at) for e in log.load()] == [
        ("tasks", "2026-06-03T18:00:00+00:00"),
        ("outbound", "2026-06-03T19:00:00+00:00"),
        ("tasks", "2026-06-03T20:00:00+00:00"),
        ("outbound", "2026-06-03T21:00:00+00:00"),
    ]
    assert all(e.status == "done" for e in log.load())


def test_redo_without_sink_leaves_outbound_pending():
    # sink 未注入（既存呼び出し）なら outbound は送信されず pending のまま（後方互換）
    log = FakeWalLogStore(entries=[_outbound_entry()])
    result = RedoPendingIntents(log, _services(), _identity, now_fn=_now).execute()
    assert result.get("resent", 0) == 0
    assert any(e.status == "pending" and e.kind == "outbound" for e in log.load())


# --- SettleOutboundIntent: 送信成功時の happy-path settle ---


def test_settle_outbound_intent_marks_sent_done():
    # 送信成功した outbound（key=created_at）を done 化し rewrite する
    log = FakeWalLogStore(
        entries=[_outbound_entry(created_at="2026-06-03T18:00:00+00:00")]
    )
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
    # （= 偽謝罪付きの複製が構造的に起きない＝実運用で観測された複製不具合の根治を直接証明）
    sink = FakeMessageSink()
    log = FakeWalLogStore(
        entries=[_outbound_entry(created_at="2026-06-03T18:00:00+00:00")]
    )
    SettleOutboundIntent(log).execute("2026-06-03T18:00:00+00:00")
    result = RedoPendingIntents(
        log, _services(), _identity, sink=sink, now_fn=_now
    ).execute()
    assert sink.sent == []
    assert result["resent"] == 0


# --- RedoPendingIntents: validate 注入と dead 隔離 ---


def _raising(kind, payload):
    """常に落ちる validate（隔離経路の駆動用）。"""
    raise ValueError("missing field: created_at")


def _knowledge_services(records=None):
    return {
        "knowledge": RegistryService(FakeRegistryStore(records=records or []), "id")
    }


def _dead_entry(key="T0001", kind="tasks", reason="bad record"):
    return WalEntry(
        key=key,
        kind=kind,
        status="dead",
        payload={"id": key},
        created_at="2026-06-03T18:00:00+00:00",
        reason=reason,
    )


def test_redo_quarantines_intent_that_fails_validation():
    # 検証に落ちた intent は registry に書かれず dead へ（reason は str(exc) そのまま）
    log = FakeWalLogStore(entries=[_entry("K1", kind="knowledge")])
    store = FakeRegistryStore(records=[])
    services = {"knowledge": RegistryService(store, "id")}
    result = RedoPendingIntents(log, services, _raising, now_fn=_now).execute()
    assert store.load() == []
    assert result["redone"] == 0
    assert result["dead"] == 1
    entry = log.load()[0]
    assert entry.status == "dead"
    assert entry.reason == "missing field: created_at"


def test_redo_bad_intent_does_not_block_other_pending():
    # 1 件の不正が他の pending の redo を道連れにしない（隔離の核心）
    def validate(kind, payload):
        if payload["id"] == "K1":
            raise ValueError("bad record")
        return payload

    log = FakeWalLogStore(
        entries=[_entry("K1", kind="knowledge"), _entry("K2", kind="knowledge")]
    )
    store = FakeRegistryStore(records=[])
    services = {"knowledge": RegistryService(store, "id")}
    result = RedoPendingIntents(log, services, validate, now_fn=_now).execute()
    assert {r["id"] for r in store.load()} == {"K2"}
    assert result["redone"] == 1
    assert result["dead"] == 1
    assert {e.key: e.status for e in log.load()} == {"K1": "dead", "K2": "done"}


def test_redo_upserts_canonical_record_not_raw_payload():
    # add_or_update に渡るのは validate の戻り値（正準 dict）であって生 payload ではない
    def canonicalize(kind, payload):
        return {**payload, "subjects": []}

    log = FakeWalLogStore(entries=[_entry("K1", kind="knowledge")])
    store = FakeRegistryStore(records=[])
    services = {"knowledge": RegistryService(store, "id")}
    RedoPendingIntents(log, services, canonicalize, now_fn=_now).execute()
    assert store.load() == [{"id": "K1", "subjects": []}]


def test_redo_does_not_revalidate_existing_dead():
    # redo は冪等: 前回隔離した dead は再検証も再 upsert もしない
    calls = []

    def validate(kind, payload):
        calls.append((kind, payload))
        return payload

    store = FakeRegistryStore(records=[])
    log = FakeWalLogStore(entries=[_dead_entry("K1", kind="knowledge")])
    services = {"knowledge": RegistryService(store, "id")}
    result = RedoPendingIntents(log, services, validate, now_fn=_now).execute()
    assert calls == []
    assert store.load() == []
    assert log.load()[0].status == "dead"
    assert log.load()[0].reason == "bad record"
    assert result["dead"] == 1


def test_redo_settles_dead_when_key_reappears_in_registry():
    # dead の出口その 1: 同 key が registry に現れれば settle が done 化（自己治癒）
    log = FakeWalLogStore(entries=[_dead_entry("K1", kind="knowledge")])
    services = _knowledge_services(records=[{"id": "K1"}])
    result = RedoPendingIntents(log, services, _identity, now_fn=_now).execute()
    assert log.load()[0].status == "done"
    assert result["dead"] == 0


def test_redo_dead_count_is_total_in_log_not_newly_quarantined():
    # dead は「今回隔離した件数」でなく「ログに残る総数」＝未履行の約束が毎起動で見える
    log = FakeWalLogStore(
        entries=[_dead_entry("K1", kind="knowledge"), _entry("K2", kind="knowledge")]
    )
    result = RedoPendingIntents(
        log, _knowledge_services(), _raising, now_fn=_now
    ).execute()
    assert result["dead"] == 2
    assert result["redone"] == 0


def test_redo_preserves_interleaved_order_with_three_statuses():
    """pending / done / dead が混在しても WAL の時系列（interleave 順）が保たれる。

    quarantine も settle も 1:1 の順序保持なので、kind 別分離→交互消費の復元は不変。
    ここが崩れると短期記憶の読み出し順が壊れる（R-34）。
    """

    def validate(kind, payload):
        if payload["id"] == "T0002":
            raise ValueError("bad record")
        return payload

    log = FakeWalLogStore(
        entries=[
            _entry("T0001", created_at="2026-06-03T18:00:00+00:00"),
            _outbound_entry(created_at="2026-06-03T19:00:00+00:00"),
            _entry("T0002", created_at="2026-06-03T20:00:00+00:00"),
            _outbound_entry(created_at="2026-06-03T21:00:00+00:00"),
        ]
    )
    services = {"tasks": RegistryService(FakeRegistryStore(records=[]), "id")}
    # sink 未注入＝outbound は pending 据え置き（三状態を一本のログに揃える）
    RedoPendingIntents(log, services, validate, now_fn=_now).execute()
    assert [(e.kind, e.created_at, e.status) for e in log.load()] == [
        ("tasks", "2026-06-03T18:00:00+00:00", "done"),
        ("outbound", "2026-06-03T19:00:00+00:00", "pending"),
        ("tasks", "2026-06-03T20:00:00+00:00", "dead"),
        ("outbound", "2026-06-03T21:00:00+00:00", "pending"),
    ]


# --- DropDeadIntent: dead の明示的な出口（pending を落とす口は開けない） ---


def test_drop_dead_removes_entry_and_rewrites():
    log = FakeWalLogStore(entries=[_dead_entry("T0001"), _entry("T0002")])
    DropDeadIntent(log).execute("tasks", "T0001")
    assert [e.key for e in log.load()] == ["T0002"]
    assert len(log.rewrite_calls) == 1


def test_drop_dead_removes_all_duplicate_dead_rows_of_same_key():
    log = FakeWalLogStore(entries=[_dead_entry("T0001"), _dead_entry("T0001")])
    DropDeadIntent(log).execute("tasks", "T0001")
    assert log.load() == []


def test_drop_dead_keeps_pending_row_of_same_key():
    # 同 (kind, key) に dead と pending が並ぶ場合、落とすのは dead だけ
    log = FakeWalLogStore(entries=[_dead_entry("T0001"), _entry("T0001")])
    DropDeadIntent(log).execute("tasks", "T0001")
    assert [(e.key, e.status) for e in log.load()] == [("T0001", "pending")]


def test_drop_dead_rejects_pending():
    # pending を落とす＝約束を黙って捨てる口は開けない（status をメッセージに載せる）
    log = FakeWalLogStore(entries=[_entry("T0001")])
    with pytest.raises(ValueError, match="pending"):
        DropDeadIntent(log).execute("tasks", "T0001")
    assert log.rewrite_calls == []


def test_drop_dead_rejects_done():
    log = FakeWalLogStore(entries=[_entry("T0001", status="done")])
    with pytest.raises(ValueError, match="done"):
        DropDeadIntent(log).execute("tasks", "T0001")


def test_drop_dead_rejects_missing_key():
    log = FakeWalLogStore(entries=[_dead_entry("T0001")])
    with pytest.raises(ValueError, match="not found"):
        DropDeadIntent(log).execute("tasks", "T9999")


def test_drop_dead_distinguishes_kind():
    # 同 key でも kind が違えば別物（reconcile の (kind, key) 照合と同じ規律）
    log = FakeWalLogStore(entries=[_dead_entry("T0001", kind="tasks")])
    with pytest.raises(ValueError, match="not found"):
        DropDeadIntent(log).execute("knowledge", "T0001")
