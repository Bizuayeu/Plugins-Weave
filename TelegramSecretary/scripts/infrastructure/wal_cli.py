"""WAL CLI ハンドラ。main.py の wal-append / wal-push / wal-redo から呼ばれる。

`registry_sync` 有効時のみ稼働（無効は no-op、後方互換）。決定論 I/O＝何を intent に
するかの判断は エージェント（重要度の世界）、ここは append/push/redo の primitive。
WAL ログは registry と同じ `registry_root` 配下に置き、同一固定ブランチへ相乗りで push する。
"""
from __future__ import annotations

import sys
from typing import Any, Optional

from adapters.wal.jsonl_wal_log_store import JsonlWalLogStore
from domain.exceptions import GitSyncError
from domain.lease import utc_now
from infrastructure.config import Config
from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_FETCH_FAILED, EXIT_OK
from infrastructure.registry_cli import (
    _REGISTRY_SPEC,
    _build_git,
    _read_json_arg,
    _service,
)
from usecases.wal import AppendWalIntent, PushWalLog, RedoPendingIntents

# WAL 対象種別は registry の全管理表種別（individuals/tasks/knowledge/abilities）。
# abilities も能力宣言（「○○できます」という対外的約束）を伴うため一様に対象（DESIGN §3.8）。
# registry_cli._REGISTRY_SPEC を SSoT とし、kind -> key_field を導出する（二重管理の解消）。
_WAL_KINDS = {k: spec[1] for k, spec in _REGISTRY_SPEC.items()}


def run_wal_append(config: Config, kind: str, args: Any) -> int:
    """intent を pending で WAL ログに追記（registry_sync 無効なら no-op）。"""
    if not config.registry_sync_enabled:
        return EXIT_OK  # WAL は registry 永続化に相乗り、無効環境では素通り
    if kind not in _WAL_KINDS:
        print(f"unknown wal kind: {kind}", file=sys.stderr)
        return EXIT_CONFIG_INVALID
    key_field = _WAL_KINDS[kind]
    try:
        payload = _read_json_arg(args)
    except (ValueError, OSError, TypeError) as exc:
        print(f"invalid wal payload: {exc}", file=sys.stderr)
        return EXIT_CONFIG_INVALID
    key = payload.get(key_field)
    if not key:
        print(f"wal payload missing key field {key_field!r}", file=sys.stderr)
        return EXIT_CONFIG_INVALID
    AppendWalIntent(JsonlWalLogStore(config.wal_log_path)).execute(
        key=key, kind=kind, payload=payload, created_at=utc_now().isoformat()
    )
    print(f"wal appended {kind} {key_field}={key}")
    return EXIT_OK


def run_wal_push(config: Config, args: Any, git=None) -> int:
    """WAL ログを commit & push（must-succeed）。push 失敗は exit 非0（送信前ゲート）。

    git 注入はテスト用、本番は config から GitCliAdapter を組み立てる。PushRejectedError は
    GitSyncError のサブクラスゆえ `except GitSyncError` 一つで（rebase 後の再失敗も含め）拾う。
    """
    if not config.registry_sync_enabled:
        return EXIT_OK
    if git is None:
        git = _build_git(config)
    message = getattr(args, "message", None) or "wal: append intent"
    try:
        PushWalLog(git, config.wal_log_path).execute(message)
    except GitSyncError as exc:
        print(f"wal push failed: {exc}", file=sys.stderr)
        return EXIT_FETCH_FAILED  # 送信前ゲート: 秘書は send-reply を打たない
    print("wal pushed")
    return EXIT_OK


def run_wal_redo(config: Config, args: Optional[Any] = None) -> int:
    """起動時に WAL pending を registry へ redo（registry_sync 有効時のみ）。返信は再送しない。"""
    if not config.registry_sync_enabled:
        return EXIT_OK
    services = {kind: _service(config, kind) for kind in _WAL_KINDS}
    result = RedoPendingIntents(
        JsonlWalLogStore(config.wal_log_path), services
    ).execute()
    print(f"wal redo: redone={result['redone']} kept={result['kept']}")
    return EXIT_OK
