"""WAL CLI ハンドラ（run_wal_append/push/redo）のテスト。registry_sync 有効/無効の分岐。"""
from __future__ import annotations

from types import SimpleNamespace

from domain.authorization import AuthorizedChats
from domain.exceptions import GitSyncError
from domain.wal import WalEntry
from infrastructure.config import Config
from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_FETCH_FAILED, EXIT_OK
from infrastructure.wal_cli import run_wal_append, run_wal_push, run_wal_redo

from adapters.registry.json_registry_store import JsonRegistryStore
from adapters.wal.jsonl_wal_log_store import JsonlWalLogStore
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


# --- run_wal_append ---

def test_append_noop_when_sync_disabled(tmp_path):
    config = _config(tmp_path, sync=False)
    args = SimpleNamespace(json='{"id": "T0001"}', json_file=None)
    assert run_wal_append(config, "tasks", args) == EXIT_OK
    assert not config.wal_log_path.exists()  # 無効なら書かない（no-op）


def test_append_writes_pending_when_enabled(tmp_path):
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json='{"id": "T0001"}', json_file=None)
    assert run_wal_append(config, "tasks", args) == EXIT_OK
    entries = JsonlWalLogStore(config.wal_log_path).load()
    assert entries[0].key == "T0001"
    assert entries[0].status == "pending"


# --- run_wal_push: must-succeed（送信前ゲート） ---

def test_push_noop_when_disabled(tmp_path):
    assert run_wal_push(_config(tmp_path, sync=False), SimpleNamespace(message=None)) == EXIT_OK


def test_push_exit_nonzero_on_failure(tmp_path):
    config = _config(tmp_path, sync=True)
    git = FakeGitSync(committed=True, push_outcomes=[GitSyncError("net down")])
    assert run_wal_push(config, SimpleNamespace(message="m"), git=git) == EXIT_FETCH_FAILED


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
            key="T0001", kind="tasks", status="pending",
            payload={"id": "T0001"}, created_at="2026-06-03T18:00:00+00:00",
        )
    )
    assert run_wal_redo(config) == EXIT_OK
    records = JsonRegistryStore(config.tasks_path).load()
    assert any(r["id"] == "T0001" for r in records)  # registry へ反映
    assert all(e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load())


# --- abilities も WAL 対象（4 表一様、DESIGN §3.8）---

def test_append_writes_abilities_pending(tmp_path):
    """abilities の add も能力宣言（対外的約束）を伴うため WAL 先行書込の対象。"""
    config = _config(tmp_path, sync=True)
    args = SimpleNamespace(json='{"id": "A1"}', json_file=None)
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
            key="A1", kind="abilities", status="pending",
            payload={"id": "A1"}, created_at="2026-06-04T18:00:00+00:00",
        )
    )
    assert run_wal_redo(config) == EXIT_OK
    records = JsonRegistryStore(config.abilities_path).load()
    assert any(r["id"] == "A1" for r in records)  # registry へ反映
    assert all(e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load())


# --- outbound kind（proactive-send 送信ロスト対策、Stage 3）---


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
            key="2026-06-03T18:00:00+00:00", kind="outbound", status="pending",
            payload={"chat_id": 100, "text": "関連トピック"},
            created_at="2026-06-03T18:00:00+00:00",
        )
    )
    sink = FakeMessageSink()
    assert run_wal_redo(config, sink=sink) == EXIT_OK
    assert len(sink.sent) == 1
    assert "念のため再送します" in sink.sent[0].text
    assert "関連トピック" in sink.sent[0].text
    assert all(
        e.status == "done" for e in JsonlWalLogStore(config.wal_log_path).load()
    )
