"""WAL CLI ハンドラ。main.py の wal-append / wal-push / wal-redo から呼ばれる。

`registry_sync` 有効時のみ稼働（無効は no-op、後方互換）。決定論 I/O＝何を intent に
するかの判断は エージェント（重要度の世界）、ここは append/push/redo の primitive。
WAL ログは registry と同じ `registry_root` 配下に置き、同一固定ブランチへ相乗りで push する。
"""
from __future__ import annotations

import sys
from typing import Any, Optional

from adapters.telegram.api_gateway import TelegramApiGateway
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
    """intent を pending で WAL ログに追記（registry_sync 無効なら no-op）。

    registry kind（individuals/tasks/knowledge/abilities）は payload の key_field をキーにする。
    outbound kind（proactive-send）は registry key を持たないため created_at をキーにする
    （reconcile 照合に乗らない＝registry redo と独立、DESIGN §3.9）。
    """
    if not config.registry_sync_enabled:
        return EXIT_OK  # WAL は registry 永続化に相乗り、無効環境では素通り
    try:
        payload = _read_json_arg(args)
    except (ValueError, OSError, TypeError) as exc:
        print(f"invalid wal payload: {exc}", file=sys.stderr)
        return EXIT_CONFIG_INVALID
    created_at = utc_now().isoformat()
    if kind == "outbound":
        # outbound は registry key を持たない。送信予定時刻（created_at）をキーにする
        if not payload.get("chat_id"):
            print("wal outbound payload missing 'chat_id'", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        key = created_at
    elif kind in _WAL_KINDS:
        key_field = _WAL_KINDS[kind]
        key = payload.get(key_field)
        if not key:
            print(f"wal payload missing key field {key_field!r}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
    else:
        print(f"unknown wal kind: {kind}", file=sys.stderr)
        return EXIT_CONFIG_INVALID
    AppendWalIntent(JsonlWalLogStore(config.wal_log_path)).execute(
        key=key, kind=kind, payload=payload, created_at=created_at
    )
    print(f"wal appended {kind} key={key}")
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


def run_wal_redo(config: Config, args: Optional[Any] = None, sink=None) -> int:
    """起動時に WAL pending を registry へ redo + outbound を1回再送（registry_sync 有効時のみ）。

    registry kind は再送しない（送信前クラッシュ分は offset 再取得が担う）。outbound kind は
    offset の安全網が無いため sink へ1回再送して done 化する（DESIGN §3.9）。sink 注入はテスト用、
    本番は config から TelegramApiGateway を組む（run_wal_push の git=None 注入と同型）。
    """
    if not config.registry_sync_enabled:
        return EXIT_OK
    services = {kind: _service(config, kind) for kind in _WAL_KINDS}
    log = JsonlWalLogStore(config.wal_log_path)
    if sink is not None:
        result = RedoPendingIntents(log, services, sink=sink).execute()
    else:
        with TelegramApiGateway(bot_token=config.bot_token) as gateway:
            result = RedoPendingIntents(log, services, sink=gateway).execute()
    print(
        f"wal redo: redone={result['redone']} resent={result['resent']} kept={result['kept']}"
    )
    return EXIT_OK
