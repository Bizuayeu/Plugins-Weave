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
from infrastructure.composition import build_git
from infrastructure.config import Config
from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_FETCH_FAILED, EXIT_OK
from infrastructure.registry_cli import (
    REGISTRY_SPEC,
    read_json_arg,
    registry_service,
)
from usecases.wal import (
    AppendWalIntent,
    PushWalLog,
    RedoPendingIntents,
    SettleOutboundIntent,
)

# WAL 対象種別は registry の全管理表種別（individuals/tasks/knowledge/abilities）。
# abilities も能力宣言（「○○できます」という対外的約束）を伴うため一様に対象（DESIGN §3.8）。
# registry_cli.REGISTRY_SPEC を SSoT とし、kind -> key_field を導出する（二重管理の解消）。
_WAL_KINDS = {k: spec.key_field for k, spec in REGISTRY_SPEC.items()}


def run_wal_append(config: Config, kind: str, args: Any) -> int:
    """intent を pending で WAL ログに追記（registry_sync 無効なら no-op）。

    registry kind（individuals/tasks/knowledge/abilities）は payload の key_field をキーにする。
    outbound kind（proactive-send）は registry key を持たないため created_at をキーにする
    （reconcile 照合に乗らない＝registry redo と独立、DESIGN §3.9）。
    """
    if not config.registry_sync_enabled:
        return EXIT_OK  # WAL は registry 永続化に相乗り、無効環境では素通り
    try:
        payload = read_json_arg(args)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        # registry_cli の add と同一の捕捉タプル（入力不正は exit 2 に統一）
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
        git = build_git(config)
    message = getattr(args, "message", None) or "wal: append intent"
    try:
        PushWalLog(git, config.wal_log_path).execute(message)
    except GitSyncError as exc:
        print(f"wal push failed: {exc}", file=sys.stderr)
        return EXIT_FETCH_FAILED  # 送信前ゲート: 秘書は send-reply を打たない
    print("wal pushed")
    return EXIT_OK


def run_wal_redo(config: Config, sink=None, git=None) -> int:
    """起動時に WAL pending を registry へ redo + outbound を1回再送（registry_sync 有効時のみ）。

    registry kind は再送しない（送信前クラッシュ分の再配信は Telegram サーバ側の
    unconfirmed セマンティクス＝新コンテナの fresh state_dir での再取得が担う）。outbound kind は
    offset の安全網が無いため sink へ1回再送して done 化する（DESIGN §3.9）。sink 注入はテスト用、
    本番は config から TelegramApiGateway を組む（run_wal_push の git=None 注入と同型）。

    **redo 後の done-marking を固定ブランチへ push する**（best-effort）。これを欠くと
    `RedoPendingIntents.execute()` の rewrite はローカル作業ツリーにしか残らず、次回起動の
    bootstrap（worktree を origin へ reset）で done が消え、remote の outbound=pending が復活し
    **4時間ごと（session_duration_sec ごと）に無限再送される**（旧バグ）。「1回だけ再送→即 done」
    の冪等性保証は done の永続化まで含めて初めて成立する。git 注入はテスト用（run_wal_push と同型）。
    """
    if not config.registry_sync_enabled:
        return EXIT_OK
    services = {kind: registry_service(config, kind) for kind in _WAL_KINDS}
    log = JsonlWalLogStore(config.wal_log_path)
    if sink is not None:
        result = RedoPendingIntents(log, services, sink=sink).execute()
    else:
        with TelegramApiGateway(bot_token=config.bot_token) as gateway:
            result = RedoPendingIntents(log, services, sink=gateway).execute()
    print(
        f"wal redo: redone={result['redone']} resent={result['resent']} kept={result['kept']}"
    )
    _persist_redo_log(config, git=git)
    return EXIT_OK


def _persist_redo_log(config: Config, git=None) -> None:
    """redo で書き戻した WAL ログ（done-marking / checkpoint）を固定ブランチへ best-effort push。

    add/remove と同じイベント駆動 best-effort（registry_sync の握る push）。push 不能なら
    ローカルに残し次回起動で再試行する。**must-succeed にしない**のは起動経路（wal-redo は
    Step 4）を git の transient 失敗で止めないため——失敗時の最悪ケースは outbound が次回再送
    （謝罪プレフィックスで社会的に無害化、DESIGN §3.9）に留まる。差分が無ければ commit が
    no-op（False）で push も走らない。
    """
    if git is None:
        git = build_git(config)
    try:
        PushWalLog(git, config.wal_log_path).execute("wal: persist redo (done-marking)")
    except GitSyncError as exc:
        print(f"wal redo persist (best-effort) skipped: {exc}", file=sys.stderr)


def run_wal_append_outbound(
    config: Config,
    chat_id: int,
    text: str,
    attachment_paths: list,
    reply_to: Optional[int],
    git=None,
) -> tuple[bool, str]:
    """outbound intent を WAL に先行書込み + push（proactive-send の送信前ゲート）。

    registry_sync 無効なら (True, "")＝WAL スキップで送信続行（後方互換）。`created_at` を
    キーに pending を書き（添付パス・reply_to も payload に載せ、再送時の添付欠落を解消）、
    must-succeed push する。push 失敗なら (False, created_at)＝呼び出し側は送信を中止する
    （§3.9 送信前ゲート）。成功なら (True, created_at)——created_at は送信成功後の settle キー。
    """
    if not config.registry_sync_enabled:
        return True, ""
    created_at = utc_now().isoformat()
    payload: dict = {"chat_id": chat_id, "text": text}
    if attachment_paths:
        payload["attachments"] = list(attachment_paths)
    if reply_to is not None:
        payload["reply_to_message_id"] = reply_to
    AppendWalIntent(JsonlWalLogStore(config.wal_log_path)).execute(
        key=created_at, kind="outbound", payload=payload, created_at=created_at
    )
    if git is None:
        git = build_git(config)
    try:
        PushWalLog(git, config.wal_log_path).execute(f"wal: outbound intent {created_at}")
    except GitSyncError as exc:
        print(f"wal outbound push failed (send aborted): {exc}", file=sys.stderr)
        return False, created_at
    return True, created_at


def run_wal_settle_outbound(config: Config, key: str, git=None) -> None:
    """送信成功した outbound intent を done 化 + push（happy-path settle、best-effort）。

    proactive-send が送信成功直後に呼ぶ。registry_sync 無効 or key 空なら no-op。
    `SettleOutboundIntent` で done 化（ローカル rewrite）後、done-marking を固定ブランチへ
    best-effort push（`_persist_redo_log` と同型——push 失敗の最悪ケースは次回 redo が done を
    再試行するだけ、送信は既に成功済みゆえ起動を止めない）。これで「成功送信が次回 redo で
    偽謝罪付き再送される」のを構造的に断つ（§3.9 happy-path settle）。
    """
    if not config.registry_sync_enabled or not key:
        return
    SettleOutboundIntent(JsonlWalLogStore(config.wal_log_path)).execute(key)
    if git is None:
        git = build_git(config)
    try:
        PushWalLog(git, config.wal_log_path).execute(f"wal: settle outbound {key}")
    except GitSyncError as exc:
        print(f"wal outbound settle persist (best-effort) skipped: {exc}", file=sys.stderr)
