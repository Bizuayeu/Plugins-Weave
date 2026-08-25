"""WAL CLI ハンドラ（run_wal_append/push/redo）のテスト。registry_sync 有効/無効の分岐。"""

from __future__ import annotations

import json
from types import SimpleNamespace

from adapters.registry.json_registry_store import JsonRegistryStore
from adapters.wal.jsonl_wal_log_store import JsonlWalLogStore
from domain.authorization import AuthorizedChats
from domain.exceptions import GitSyncError
from domain.registry import Knowledge
from domain.wal import WalEntry
from infrastructure.config import Config
from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_FETCH_FAILED, EXIT_OK
from infrastructure.wal_cli import (
    run_wal_append,
    run_wal_append_outbound,
    run_wal_drop,
    run_wal_push,
    run_wal_redo,
    run_wal_settle_outbound,
)
from tests.usecases.fakes import FakeGitSync, FakeMessageSink


def _config(tmp_path, sync=True):
    return Config(
        bot_token="x",
        authorized_chats=AuthorizedChats.from_iterable([1]),
        state_dir=tmp_path / "state",
        session_duration_sec=3600,
        registry_dir=tmp_path / "registry",
        registry_sync_enabled=sync,
    )


# 1.11.0 以降 registry kind の payload は入口で値オブジェクト検証を通るため、テストも
# 正準形（必須項目を満たす payload）を配る——「WAL は緩い」テストが仕様の証拠にならないよう。
_TS = "2026-06-03T18:00:00+00:00"


def _task(key="T0001"):
    return {
        "id": key,
        "title": "打ち合わせ資料",
        "status": "open",
        "priority": "high",
        "requester": "依頼者",
        "created_at": _TS,
        "updated_at": _TS,
    }


def _record(kind, key):
    """kind ごとの必須項目を満たす最小レコード（key_field は常に id）。"""
    base = {"id": key, "created_at": _TS, "updated_at": _TS}
    extra = {
        "tasks": {
            "title": "打ち合わせ資料",
            "status": "open",
            "priority": "high",
            "requester": "依頼者",
        },
        "abilities": {"name": "占術鑑定"},
        "profile": {"subject": "依頼者"},
        "goals": {"title": "資金繰りを整える"},
        "steps": {"goal_id": "g1", "title": "残高を数える"},
        "subjects": {"label": key},
    }
    return {**base, **extra.get(kind, {})}


# --- run_wal_append ---


def test_append_noop_when_sync_disabled(tmp_path):
    config = _config(tmp_path, sync=False)
    args = SimpleNamespace(json='{"id": "T0001"}', json_file=None)
    assert run_wal_append(config, "tasks", args) == EXIT_OK
    assert not config.wal_log_path.exists()  # 無効なら書かない（no-op）


def test_append_writes_pending_when_enabled(tmp_path):
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json=json.dumps(_task()), json_file=None)
    assert run_wal_append(config, "tasks", args) == EXIT_OK
    entries = JsonlWalLogStore(config.wal_log_path).load()
    assert entries[0].key == "T0001"
    assert entries[0].status == "pending"


# WAL は「送信前に intent を先行 push する must-succeed 経路」なので、入口で弾けない不正が
# あると壊れたログを push しに行く。入力不正はすべて exit 2 で、ログを書く前に止める。


def test_append_rejects_malformed_json_before_writing(tmp_path):
    """壊れた JSON は exit 2（registry_cli の add と同じ捕捉タプル・同じ exit code）。"""
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json="{not json", json_file=None)
    assert run_wal_append(config, "tasks", args) == EXIT_CONFIG_INVALID
    assert not config.wal_log_path.exists()


def test_append_rejects_registry_payload_without_its_key_field(tmp_path):
    """registry kind は key_field（tasks なら id）が無いと弾く——キー無しは redo で照合できない。"""
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json='{"title": "id の無いレコード"}', json_file=None)
    assert run_wal_append(config, "tasks", args) == EXIT_CONFIG_INVALID
    assert not config.wal_log_path.exists()


def test_append_rejects_unknown_kind(tmp_path):
    """未知の kind は弾く（redo 側に対応する表が無く、書けても復元されない）。"""
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json='{"id": "X0001"}', json_file=None)
    assert run_wal_append(config, "nonexistent", args) == EXIT_CONFIG_INVALID
    assert not config.wal_log_path.exists()


# --- run_wal_push: must-succeed（送信前ゲート） ---


def test_push_noop_when_disabled(tmp_path):
    assert (
        run_wal_push(_config(tmp_path, sync=False), SimpleNamespace(message=None))
        == EXIT_OK
    )


def test_push_exit_nonzero_on_failure(tmp_path):
    config = _config(tmp_path, sync=True)
    git = FakeGitSync(committed=True, push_outcomes=[GitSyncError("net down")])
    assert (
        run_wal_push(config, SimpleNamespace(message="m"), git=git) == EXIT_FETCH_FAILED
    )


def test_push_ok_on_success(tmp_path):
    config = _config(tmp_path, sync=True)
    git = FakeGitSync(committed=True, push_outcomes=[None])
    assert run_wal_push(config, SimpleNamespace(message="m"), git=git) == EXIT_OK


# --- run_wal_redo ---


def test_redo_noop_when_disabled(tmp_path):
    assert run_wal_redo(_config(tmp_path, sync=False)) == EXIT_OK


def test_redo_reconciles_pending_into_registry(tmp_path):
    config = _config(tmp_path, sync=True)
    # WAL に pending（registry 空）→ redo で registry に upsert され、entry は done 化
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key="T0001",
            kind="tasks",
            status="pending",
            payload=_task(),
            created_at=_TS,
        )
    )
    assert run_wal_redo(config, git=FakeGitSync()) == EXIT_OK
    records = JsonRegistryStore(config.tasks_path).load()
    assert any(r["id"] == "T0001" for r in records)  # registry へ反映
    assert all(e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load())


# --- abilities も WAL 対象（4 表一様、DESIGN §3.8）---


def test_append_writes_abilities_pending(tmp_path):
    """abilities の add も能力宣言（対外的約束）を伴うため WAL 先行書込の対象。"""
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json=json.dumps(_record("abilities", "A1")), json_file=None)
    assert run_wal_append(config, "abilities", args) == EXIT_OK
    entries = JsonlWalLogStore(config.wal_log_path).load()
    assert entries[0].key == "A1"
    assert entries[0].kind == "abilities"
    assert entries[0].status == "pending"


def test_redo_reconciles_abilities_pending_into_registry(tmp_path):
    """起動時 redo が abilities の pending intent も registry へ反映し done 化する。"""
    config = _config(tmp_path, sync=True)
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key="A1",
            kind="abilities",
            status="pending",
            payload=_record("abilities", "A1"),
            created_at="2026-06-04T18:00:00+00:00",
        )
    )
    assert run_wal_redo(config, git=FakeGitSync()) == EXIT_OK
    records = JsonRegistryStore(config.abilities_path).load()
    assert any(r["id"] == "A1" for r in records)  # registry へ反映
    assert all(e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load())


# --- P/A 軸 3 表も WAL 対象（REGISTRY_SPEC 導出で自動拡張、二重管理なし）---


def test_wal_append_accepts_new_kinds(tmp_path):
    """profile/goals/steps の add も WAL 先行書込の対象（_WAL_KINDS は REGISTRY_SPEC 導出）。"""
    config = _config(tmp_path, sync=True)
    for kind in ("profile", "goals", "steps"):
        payload = json.dumps(_record(kind, f"{kind}-1"), ensure_ascii=False)
        args = SimpleNamespace(json=payload, json_file=None)
        assert run_wal_append(config, kind, args) == EXIT_OK
    entries = JsonlWalLogStore(config.wal_log_path).load()
    assert [e.kind for e in entries] == ["profile", "goals", "steps"]
    assert all(e.status == "pending" for e in entries)


def test_wal_append_accepts_the_subjects_kind(tmp_path):
    """8 表目 subjects も WAL 対象（REGISTRY_SPEC への 1 行で choices ごと追従する）。"""
    config = _config(tmp_path, sync=True)
    payload = json.dumps(_record("subjects", "馬"), ensure_ascii=False)
    args = SimpleNamespace(json=payload, json_file=None)
    assert run_wal_append(config, "subjects", args) == EXIT_OK
    entries = JsonlWalLogStore(config.wal_log_path).load()
    assert [(e.kind, e.key) for e in entries] == [("subjects", "馬")]


def test_wal_redo_upserts_new_kinds(tmp_path):
    """起動時 redo が新3表の pending intent も registry へ反映し done 化する。"""
    config = _config(tmp_path, sync=True)
    log = JsonlWalLogStore(config.wal_log_path)
    log.append(
        WalEntry(
            key="pf1",
            kind="profile",
            status="pending",
            payload=_record("profile", "pf1"),
            created_at="2026-06-12T00:00:00+00:00",
        )
    )
    log.append(
        WalEntry(
            key="g1",
            kind="goals",
            status="pending",
            payload=_record("goals", "g1"),
            created_at="2026-06-12T00:00:01+00:00",
        )
    )
    assert run_wal_redo(config, git=FakeGitSync()) == EXIT_OK
    assert any(r["id"] == "pf1" for r in JsonRegistryStore(config.profile_path).load())
    assert any(r["id"] == "g1" for r in JsonRegistryStore(config.goals_path).load())
    assert all(e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load())


# --- outbound kind（proactive-send 送信ロスト対策）---


def test_append_writes_outbound_pending(tmp_path):
    """outbound kind は key_field 不在ゆえ created_at をキーに pending 追記。"""
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json='{"chat_id": 100, "text": "hi"}', json_file=None)
    assert run_wal_append(config, "outbound", args) == EXIT_OK
    entries = JsonlWalLogStore(config.wal_log_path).load()
    assert entries[0].kind == "outbound"
    assert entries[0].status == "pending"
    assert entries[0].payload["chat_id"] == 100


def test_append_outbound_missing_chat_id_is_config_invalid(tmp_path):
    """outbound payload に chat_id が無ければ入力不正（exit 2）。"""
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json='{"text": "hi"}', json_file=None)
    assert run_wal_append(config, "outbound", args) == EXIT_CONFIG_INVALID


def test_redo_resends_outbound_via_sink(tmp_path):
    """redo が outbound pending を sink へ1回再送（謝罪プレフィックス）し done 化する。"""
    config = _config(tmp_path, sync=True)
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key="2026-06-03T18:00:00+00:00",
            kind="outbound",
            status="pending",
            payload={"chat_id": 100, "text": "関連トピック"},
            created_at="2026-06-03T18:00:00+00:00",
        )
    )
    sink = FakeMessageSink()
    assert run_wal_redo(config, sink=sink, git=FakeGitSync()) == EXIT_OK
    assert len(sink.sent) == 1
    assert "お届けします" in sink.sent[0].text
    assert (
        "システムが落ちていた" not in sink.sent[0].text
    )  # 障害断定の除去（偽謝罪の根治）
    assert "関連トピック" in sink.sent[0].text
    assert all(e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load())


# --- 回帰: redo の done-marking を固定ブランチへ push（4時間ごと無限再送バグの再発防止）---


def test_redo_persists_done_marking_to_branch(tmp_path):
    """redo が outbound を再送して done 化した後、その done-marking を commit & push する。

    push しないと次回起動の reset で done が消え outbound=pending が復活＝無限再送（旧バグ）。
    redo は done の永続化まで含めて完了する。
    """
    config = _config(tmp_path, sync=True)
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key="2026-06-03T18:00:00+00:00",
            kind="outbound",
            status="pending",
            payload={"chat_id": 100, "text": "感想"},
            created_at="2026-06-03T18:00:00+00:00",
        )
    )
    git = FakeGitSync(committed=True, push_outcomes=[None])
    assert run_wal_redo(config, sink=FakeMessageSink(), git=git) == EXIT_OK
    assert git.push_calls == 1  # done-marking が固定ブランチへ push された
    assert git.commit_calls and config.wal_log_path in git.commit_calls[0][0]


def test_redo_persist_is_best_effort_on_push_failure(tmp_path):
    """push 失敗（transient）でも redo は exit 0（起動経路を git 失敗で止めない＝best-effort）。"""
    config = _config(tmp_path, sync=True)
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key="2026-06-03T18:00:00+00:00",
            kind="outbound",
            status="pending",
            payload={"chat_id": 100, "text": "感想"},
            created_at="2026-06-03T18:00:00+00:00",
        )
    )
    git = FakeGitSync(
        committed=True,
        push_outcomes=[GitSyncError("net down"), GitSyncError("still down")],
    )
    assert run_wal_redo(config, sink=FakeMessageSink(), git=git) == EXIT_OK


# --- outbound happy-path settle ヘルパ（proactive-send 内包）---


def test_append_outbound_helper_noop_when_sync_disabled(tmp_path):
    # registry_sync 無効なら WAL スキップ＝(True, "")（送信は続行＝後方互換）
    ok, key = run_wal_append_outbound(
        _config(tmp_path, sync=False), 100, "hi", [], None
    )
    assert ok is True and key == ""


def test_append_outbound_helper_writes_pending_and_pushes(tmp_path):
    # 送信前ゲート: pending を created_at キーで書き、添付パス・reply_to も payload に載せる
    config = _config(tmp_path, sync=True)
    git = FakeGitSync(committed=True, push_outcomes=[None])
    ok, key = run_wal_append_outbound(config, 100, "hi", ["/tmp/a.png"], 42, git=git)
    assert ok is True and key  # created_at が返る（settle のキー）
    entry = JsonlWalLogStore(config.wal_log_path).load()[0]
    assert entry.kind == "outbound" and entry.status == "pending"
    assert entry.payload["chat_id"] == 100
    assert entry.payload["attachments"] == [
        "/tmp/a.png"
    ]  # 添付欠落の解消（再送忠実性）
    assert entry.payload["reply_to_message_id"] == 42
    assert git.push_calls == 1  # must-succeed push


def test_append_outbound_helper_returns_false_on_push_failure(tmp_path):
    # push 失敗（must-succeed）→ ok=False（呼び出し側は送信を中止＝送信前ゲート）
    config = _config(tmp_path, sync=True)
    git = FakeGitSync(
        committed=True,
        push_outcomes=[GitSyncError("net down"), GitSyncError("still down")],
    )
    ok, key = run_wal_append_outbound(config, 100, "hi", [], None, git=git)
    assert ok is False and key  # append 済み（created_at は返す）


def test_settle_outbound_helper_marks_done_and_pushes(tmp_path):
    config = _config(tmp_path, sync=True)
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key="2026-06-03T18:00:00+00:00",
            kind="outbound",
            status="pending",
            payload={"chat_id": 100, "text": "hi"},
            created_at="2026-06-03T18:00:00+00:00",
        )
    )
    git = FakeGitSync(committed=True, push_outcomes=[None])
    run_wal_settle_outbound(config, "2026-06-03T18:00:00+00:00", git=git)
    assert all(e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load())
    assert git.push_calls == 1  # done-marking を固定ブランチへ永続化


def test_settle_outbound_helper_noop_when_sync_disabled(tmp_path):
    # sync 無効なら no-op（WAL 不在環境で settle を呼んでも安全＝例外を出さない）
    run_wal_settle_outbound(_config(tmp_path, sync=False), "any-key")


def test_settle_outbound_helper_best_effort_on_push_failure(tmp_path):
    # settle の push 失敗は best-effort（送信は既に成功済み、done はローカルに残り次回 redo で再試行）
    config = _config(tmp_path, sync=True)
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key="k",
            kind="outbound",
            status="pending",
            payload={"chat_id": 100, "text": "hi"},
            created_at="2026-06-03T18:00:00+00:00",
        )
    )
    git = FakeGitSync(
        committed=True, push_outcomes=[GitSyncError("down"), GitSyncError("down")]
    )
    run_wal_settle_outbound(config, "k", git=git)  # 例外を投げない
    assert all(e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load())


# --- v1.11.0: wal-append の入口検証と正準化（書き込み三口の検証を一本化）---


def _knowledge_payload(**over):
    raw = {
        "id": "K1",
        "topic": "主題",
        "category": "method",
        "created_at": _TS,
        "updated_at": _TS,
    }
    raw.update(over)
    return raw


def test_append_rejects_a_payload_that_fails_record_validation(tmp_path, capsys):
    """値オブジェクト検証に落ちる payload はログを書く前に exit 2（add と同じ捕捉タプル）。

    key_field はあるが必須項目を欠く payload は、従来は素通りして pending として書かれ、
    起動時 redo で初めて落ちていた。書き込み口の三つ目として入口で止める。
    """
    config = _config(tmp_path, sync=True)
    raw = _knowledge_payload()
    del raw["created_at"]
    args = SimpleNamespace(json=json.dumps(raw, ensure_ascii=False), json_file=None)
    assert run_wal_append(config, "knowledge", args) == EXIT_CONFIG_INVALID
    assert "invalid knowledge wal payload: 'created_at'" in capsys.readouterr().err
    assert not config.wal_log_path.exists()  # ログを書く前に止める


def test_append_writes_the_canonical_payload(tmp_path):
    """書かれる payload は生入力ではなく正準形（`subjects` 省略が `[]` で載る等）。

    redo が upsert するのは WAL の payload なので、正準化を入口で済ませておけば
    「WAL 経由で入ったレコードだけ形が違う」表を作らずに済む。
    """
    config = _config(tmp_path, sync=True)
    raw = _knowledge_payload()
    args = SimpleNamespace(json=json.dumps(raw, ensure_ascii=False), json_file=None)
    assert run_wal_append(config, "knowledge", args) == EXIT_OK
    entry = JsonlWalLogStore(config.wal_log_path).load()[0]
    assert entry.payload == Knowledge.from_dict(raw).to_dict()
    assert entry.payload["subjects"] == []  # 省略項目が既定で埋まっている


# --- v1.11.0: redo の validator 注入と dead 報告 ---


def test_redo_quarantines_an_invalid_pending_as_dead(tmp_path, capsys):
    """検証に落ちた pending は dead へ隔離し、registry は汚さず exit 0 のまま起動を続ける。

    1.11.0 未満で書かれた（＝入口検証を通っていない）pending が初回 redo で捕まる経路。
    dead はログに残り、件数は stdout・理由は stderr に出る（毎起動で目に入る）。
    """
    config = _config(tmp_path, sync=True)
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key="T0001",
            kind="tasks",
            status="pending",
            payload={"id": "T0001", "titel": "typo したキー"},
            created_at=_TS,
        )
    )
    git = FakeGitSync(committed=True, push_outcomes=[None])
    assert run_wal_redo(config, git=git) == EXIT_OK  # 起動経路は止めない
    assert not JsonRegistryStore(config.tasks_path).load()  # registry は不変
    entries = JsonlWalLogStore(config.wal_log_path).load()
    assert [e.status for e in entries] == ["dead"]
    assert "unknown field(s): titel" in entries[0].reason
    captured = capsys.readouterr()
    assert "dead=1" in captured.out
    assert "wal redo: dead tasks key=T0001:" in captured.err
    assert "unknown field(s): titel" in captured.err
    assert git.push_calls == 1  # done-marking と同じ best-effort 永続化


# --- v1.11.0: wal-drop（dead の明示的な出口）---


def _dead_log(config, key="T0001", kind="tasks", status="dead"):
    JsonlWalLogStore(config.wal_log_path).append(
        WalEntry(
            key=key,
            kind=kind,
            status=status,
            payload={"id": key},
            created_at=_TS,
            reason="ValueError: unknown field(s): titel" if status == "dead" else "",
        )
    )


def test_drop_noop_when_sync_disabled(tmp_path):
    assert run_wal_drop(_config(tmp_path, sync=False), "tasks", "T0001") == EXIT_OK


def test_drop_removes_the_dead_entry_and_pushes(tmp_path, capsys):
    """dead を落として must-succeed push（操作者の明示行為ゆえ push 失敗を握らない）。"""
    config = _config(tmp_path, sync=True)
    _dead_log(config)
    git = FakeGitSync(committed=True, push_outcomes=[None])
    assert run_wal_drop(config, "tasks", "T0001", git=git) == EXIT_OK
    assert not JsonlWalLogStore(config.wal_log_path).load()
    assert git.push_calls == 1
    assert "wal dropped tasks key=T0001" in capsys.readouterr().out


def test_drop_exit_nonzero_when_push_fails(tmp_path):
    """push 失敗は exit 1（wal-push と同じ）——「落としたのに remote に残る」を黙らせない。"""
    config = _config(tmp_path, sync=True)
    _dead_log(config)
    git = FakeGitSync(committed=True, push_outcomes=[GitSyncError("net down")])
    assert run_wal_drop(config, "tasks", "T0001", git=git) == EXIT_FETCH_FAILED


def test_drop_rejects_a_pending_entry(tmp_path, capsys):
    """pending は落とせない（果たされていない約束を黙って捨てる口を作らない）。"""
    config = _config(tmp_path, sync=True)
    _dead_log(config, status="pending")
    git = FakeGitSync(committed=True, push_outcomes=[None])
    assert run_wal_drop(config, "tasks", "T0001", git=git) == EXIT_CONFIG_INVALID
    assert "not dead" in capsys.readouterr().err
    assert JsonlWalLogStore(config.wal_log_path).load()  # 残っている
    assert git.push_calls == 0  # 落としていないので push もしない


def test_drop_rejects_a_missing_entry(tmp_path, capsys):
    """不在キーは exit 2（打ち間違いを成功として返さない）。"""
    config = _config(tmp_path, sync=True)
    git = FakeGitSync(committed=True, push_outcomes=[None])
    assert run_wal_drop(config, "tasks", "NOPE", git=git) == EXIT_CONFIG_INVALID
    assert "not found" in capsys.readouterr().err
