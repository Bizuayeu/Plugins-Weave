"""TelegramSecretary CLI entrypoint。subcommands を argparse で分岐。"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from adapters.state.emitter import StdoutEventEmitter
from adapters.state.json_state_store import JsonLeaseStore, JsonOffsetStore
from adapters.telegram.api_gateway import TelegramApiGateway
from domain.exceptions import (
    AttachmentNotFound,
    AttachmentTooLarge,
    AuthFailureError,
    LeaseConflictError,
    TelegramSecretaryError,
)
from domain.lease import utc_now
from domain.watch_window import WatchWindow
from domain.models import OutboundMessage
from domain.outbound import OutboundAttachment
from infrastructure.composition import MediaStack, build_media_stack, load_config
from infrastructure.config import Config
from infrastructure.exit_codes import (
    EXIT_AUTH_FAILED,
    EXIT_CONFIG_INVALID,
    EXIT_FETCH_FAILED,
    EXIT_LEASE_CONFLICT,
    EXIT_OK,
)
from infrastructure.media_cleanup import cleanup_media_dir
from infrastructure.registry_cli import run_registry_command, run_registry_fetch
from infrastructure.wal_cli import (
    run_wal_append,
    run_wal_append_outbound,
    run_wal_push,
    run_wal_redo,
    run_wal_settle_outbound,
)
from usecases.acquire_lease import AcquireLease
from usecases.fetch_authorized_updates import FetchAuthorizedUpdates
from usecases.release_lease import ReleaseLease
from usecases.renew_lease import RenewLease
from usecases.proactive_send import ProactiveSend
from usecases.send_reply import SendReply

# 終了コードは infrastructure/exit_codes.py が SSoT。後方互換のため re-export
# （test_main.py / docs の `from main import EXIT_*` を温存）。
__all__ = [
    "EXIT_OK",
    "EXIT_FETCH_FAILED",
    "EXIT_CONFIG_INVALID",
    "EXIT_AUTH_FAILED",
    "EXIT_LEASE_CONFLICT",
    "main",
]


class _ConfigInvalid(Exception):
    """config ロード失敗を CLI 境界へ伝える内部シグナル。

    EnvironmentError は Python では OSError の別名であり、ハンドラ全体を
    `except EnvironmentError` で包むと read_text 等の無関係な OSError まで
    config エラーへ誤変換する。専用例外にして main() で 1 度だけ
    EXIT_CONFIG_INVALID へ変換し、捕捉範囲を config ロードに限定する。
    """


def _load_config() -> Config:
    """env から Config を構築（fail-fast）。失敗は stderr に出して _ConfigInvalid を送出。

    旧 union (`Config | int`) を廃止。EnvironmentError の捕捉はこの 1 点に限定し、
    各ハンドラの `if isinstance(config, int): return config` 重複を消す。
    """
    try:
        return load_config()
    except EnvironmentError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        raise _ConfigInvalid from None


def _session_owner(arg_owner: str | None) -> str:
    return (
        arg_owner
        or os.environ.get("TELEGRAM_SECRETARY_SESSION_ID")
        or f"session-{uuid.uuid4().hex[:8]}"
    )


def cmd_validate_config(_: argparse.Namespace) -> int:
    config = _load_config()
    print(
        f"ok: bot_token=set "
        f"authorized_chats={len(config.authorized_chats.chat_ids)} "
        f"state_dir={config.state_dir} "
        f"session_duration_sec={config.session_duration_sec}"
    )
    return EXIT_OK


def cmd_show_config(_: argparse.Namespace) -> int:
    """現在の設定を read-only 表示（秘匿はマスク）。未設定でも exit 0（設定確認パネル）。

    validate-config は「設定が正しいか」を exit code で判定する gate。show-config は
    「今どう設定されているか」を人間が眺める read-only パネルで、未設定でも 0 を返す。
    """
    try:
        config = load_config()
    except EnvironmentError as exc:
        print(f"config not ready: {exc}")
        return EXIT_OK
    print("bot_token: set")  # ロード成功＝from_sources が必須チェック済み。値は出さない（秘匿）
    print(f"authorized_chats: {len(config.authorized_chats.chat_ids)}")
    print(f"state_dir: {config.state_dir}")
    print(f"session_duration_sec: {config.session_duration_sec}")
    print(f"agent_name: {config.agent_name or '(unset)'}")
    print(f"private_dir: {config.private_dir or '(unset)'}")
    lease = JsonLeaseStore(config.state_dir).load()
    print(f"lease: {('owner=' + lease.owner) if lease else '(none)'}")
    return EXIT_OK


def cmd_init_config(args: argparse.Namespace) -> int:
    """引数から <INSTALL_DIR>/config.json を生成（決定論 I/O）。

    対話的な値収集は `/telegram-secretary` skill（重要度の世界）が担い、CLI は決定論 I/O に徹する
    （DESIGN.md §3.4）。既存ファイルは --force 無しでは上書きしない。
    """
    from domain.session_config import SessionDuration
    from infrastructure.config import _default_config_path

    try:
        SessionDuration.from_seconds(args.session_duration_sec)
    except ValueError as exc:
        print(f"invalid session_duration_sec: {exc}", file=sys.stderr)
        return EXIT_CONFIG_INVALID

    path = _default_config_path()
    if path.exists() and not args.force:
        print(
            f"config.json already exists at {path} (use --force to overwrite)",
            file=sys.stderr,
        )
        return EXIT_CONFIG_INVALID

    data: dict = {"session_duration_sec": args.session_duration_sec}
    if args.agent_name:
        data["agent_name"] = args.agent_name
    if args.private_dir:
        data["private_dir"] = args.private_dir
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote config.json to {path}")
    return EXIT_OK


def cmd_lease(args: argparse.Namespace) -> int:
    config = _load_config()
    store = JsonLeaseStore(config.state_dir)
    owner = _session_owner(args.owner)
    now = utc_now()
    try:
        if args.action == "acquire":
            lease = AcquireLease(store).execute(owner=owner, now=now, ttl_seconds=args.ttl)
            print(f"acquired owner={lease.owner} ttl={lease.ttl_seconds}")
        elif args.action == "renew":
            lease = RenewLease(store).execute(owner=owner, now=now)
            print(f"renewed owner={lease.owner} heartbeat={lease.heartbeat.isoformat()}")
        elif args.action == "release":
            ReleaseLease(store).execute(owner=owner)
            print(f"released owner={owner}")
    except LeaseConflictError as exc:
        print(f"lease conflict: {exc}", file=sys.stderr)
        return EXIT_LEASE_CONFLICT
    return EXIT_OK


def cmd_poll(args: argparse.Namespace) -> int:
    config = _load_config()

    offset_store = JsonOffsetStore(config.state_dir)
    emitter = StdoutEventEmitter()
    download_results: list = []
    render_results: list = []
    with TelegramApiGateway(bot_token=config.bot_token) as gateway:
        uc = FetchAuthorizedUpdates(gateway, offset_store, config.authorized_chats)
        try:
            updates = uc.execute(timeout_seconds=args.timeout)
        except AuthFailureError as exc:
            print(f"auth failure: {exc}", file=sys.stderr)
            return EXIT_AUTH_FAILED
        except TelegramSecretaryError as exc:
            print(f"fetch failed: {exc}", file=sys.stderr)
            return EXIT_FETCH_FAILED

        # Heavy モード: media を持つ update があれば download → render。
        # poll/watch 共通の Composition Root build_media_stack で配線（transcriber/pdf は
        # 未導入なら None で組み skipped にフォールバック）。
        if config.media_enable_download and any(u.update.media for u in updates):
            stack = build_media_stack(config, gateway)
            try:
                download_results = stack.download_uc.execute(
                    updates,
                    config.state_dir / "media",
                    config.media_max_size_bytes,
                )
                render_results = stack.render_uc.execute(download_results)
            finally:
                stack.downloader.close()

    for u in updates:
        emitter.emit(
            u, download_results=download_results, render_results=render_results
        )
    return EXIT_OK


@dataclass
class _CycleOutcome:
    """1 watch サイクルの結果。exit_code 非 None ならループは即その値で return する。"""

    exit_code: Optional[int]
    had_messages: bool


class _LazyMediaStack:
    """watch ループ用の media stack 遅延ホルダ（FINDING A）。

    media を初めて受けたサイクルで build_media_stack を 1 度だけ呼び、以降使い回す
    （MarkItDown の magika model load が重いので毎サイクル作り直さない）。media を受けない
    常駐では構築せず httpx だけで起動できる（fresh container で markitdown/moonshine 未導入でも落ちない）。
    """

    def __init__(self, config: Config, gateway) -> None:
        self._config = config
        self._gateway = gateway
        self._stack: Optional[MediaStack] = None

    def ensure(self) -> MediaStack:
        if self._stack is None:
            self._stack = build_media_stack(self._config, self._gateway)
        return self._stack

    def close(self) -> None:
        if self._stack is not None:
            self._stack.downloader.close()


def _run_watch_cycle(
    uc: FetchAuthorizedUpdates,
    renew: RenewLease,
    emitter: StdoutEventEmitter,
    owner: str,
    config: Config,
    window: WatchWindow,
    args: argparse.Namespace,
    media_target_dir: Path,
    media: _LazyMediaStack,
) -> _CycleOutcome:
    """watch の 1 サイクル（poll_timeout 丸め → fetch → media → emit → renew）。

    制御フローは戻り値で表現する（ループ側を薄く保つ）:
    - AuthFailure → exit_code=EXIT_AUTH_FAILED（renew せず即終了）
    - transient fetch error → emit を飛ばすが renew は実行（heartbeat 維持、原実装の try/else 外 renew に準拠）
    - lease 喪失 → exit_code=EXIT_LEASE_CONFLICT
    - 正常 → exit_code=None, had_messages
    """
    # 最終サイクルが bash timeout を超えないよう long-poll を残り窓に丸める（FINDING C）。
    # max_duration + timeout が bash_timeout/1000 を超えると、厳密 foreground では window 満了を
    # 超えて回り SIGTERM される（Phase 2 実測 603s=580+timeout）。残り窓に丸めれば値(580/30)に
    # 依存せず max_duration + timeout < bash_timeout の不変条件を保つ。
    poll_timeout = args.timeout
    if window.max_duration_seconds > 0:
        remaining = window.remaining_seconds(utc_now())
        if remaining < poll_timeout:
            poll_timeout = max(1, int(remaining))

    fetch_ok = True
    updates: list = []
    try:
        updates = uc.execute(timeout_seconds=poll_timeout)
    except AuthFailureError as exc:
        print(f"auth failure: {exc}", file=sys.stderr)
        return _CycleOutcome(exit_code=EXIT_AUTH_FAILED, had_messages=False)
    except TelegramSecretaryError as exc:
        # 一時的エラーはログして次サイクルへ（renew は下で実行し heartbeat を維持）
        print(f"transient fetch error: {exc}", file=sys.stderr)
        fetch_ok = False

    had_messages = False
    if fetch_ok:
        download_results: list = []
        render_results: list = []
        if config.media_enable_download and any(u.update.media for u in updates):
            stack = media.ensure()
            download_results = stack.download_uc.execute(
                updates,
                media_target_dir,
                config.media_max_size_bytes,
            )
            render_results = stack.render_uc.execute(download_results)
        for u in updates:
            emitter.emit(
                u,
                download_results=download_results,
                render_results=render_results,
            )
        had_messages = bool(updates)

    # アイドル時も heartbeat を維持。lease を失っていたら自己治癒で即終了
    try:
        renew.execute(owner=owner, now=utc_now())
    except LeaseConflictError as exc:
        print(f"lease lost during watch: {exc}", file=sys.stderr)
        return _CycleOutcome(exit_code=EXIT_LEASE_CONFLICT, had_messages=had_messages)
    return _CycleOutcome(exit_code=None, had_messages=had_messages)


def cmd_watch(args: argparse.Namespace) -> int:
    config = _load_config()

    offset_store = JsonOffsetStore(config.state_dir)
    lease_store = JsonLeaseStore(config.state_dir)
    emitter = StdoutEventEmitter()
    owner = _session_owner(args.owner)
    iterations = 0
    window = WatchWindow(started_at=utc_now(), max_duration_seconds=args.max_duration)
    media_target_dir = config.state_dir / "media"

    with TelegramApiGateway(bot_token=config.bot_token) as gateway:
        uc = FetchAuthorizedUpdates(gateway, offset_store, config.authorized_chats)
        renew = RenewLease(lease_store)
        media = _LazyMediaStack(config, gateway)
        try:
            while True:
                outcome = _run_watch_cycle(
                    uc,
                    renew,
                    emitter,
                    owner,
                    config,
                    window,
                    args,
                    media_target_dir,
                    media,
                )
                if outcome.exit_code is not None:
                    return outcome.exit_code

                iterations += 1
                # Stage 6.5 follow-up: N サイクル毎に cleanup hook（0=無効、default 120 ≒ 1h with timeout=30s）
                if (
                    args.cleanup_interval > 0
                    and iterations % args.cleanup_interval == 0
                ):
                    cleanup_media_dir(
                        media_target_dir,
                        config.media_retention_hours * 3600,
                    )
                if args.max_iterations and iterations >= args.max_iterations:
                    break
                if window.is_expired(utc_now()):
                    break
                if args.exit_on_message and outcome.had_messages:
                    break
        finally:
            media.close()
    return EXIT_OK


def cmd_cleanup_media(args: argparse.Namespace) -> int:
    """`state_dir/media/` 配下で `media_retention_hours` 超過のファイルを削除。

    Stage 6.5 follow-up: 単独実行用エンドポイント。cloud routine 外で
    cron 起動するか、人手で叩いて掃除する用途。
    """
    config = _load_config()
    target_dir = config.state_dir / "media"
    retention_seconds = config.media_retention_hours * 3600
    removed = cleanup_media_dir(target_dir, retention_seconds)
    print(f"cleaned {removed} files from {target_dir}")
    return EXIT_OK


def _parse_page_range(spec: str) -> tuple[int, int]:
    """'21-22'(1-indexed inclusive) → (20, 22) の 0-indexed [start, end)。

    '21' 単体 → (20, 21)。'21-' → (20, 大) で末尾まで（rasterize_pages 側が
    実ページ数でクランプするので上限ははみ出して良い）。
    """
    spec = spec.strip()
    if "-" in spec:
        lo_s, hi_s = spec.split("-", 1)
        start = int(lo_s) - 1
        end = int(hi_s) if hi_s.strip() else 10 ** 9
    else:
        start = int(spec) - 1
        end = start + 1
    return max(0, start), end


def cmd_render_pdf(args: argparse.Namespace) -> int:
    """オンデマンド PDF 抽出: --text 全文テキスト / --pages N-M 個別ページ画像化。

    エージェントが画像 Vision で大枠把握後（ROUTINE_PROMPT）、①全文テキスト or ②個別ページ
    （cap 超の 21 枚目以降含む）を要求した時に叩く。結果は JSON 1 行で stdout。
    """
    config = _load_config()

    path = Path(args.path)
    if not path.exists():
        print(f"render-pdf: file not found: {path.name}", file=sys.stderr)
        return EXIT_CONFIG_INVALID

    from adapters.render.pdf_renderer import PdfRenderer

    renderer = PdfRenderer(image_max_pages=config.pdf_image_max_pages)
    if args.text:
        result = renderer.extract_text(path)
        print(
            json.dumps(
                {
                    "mode": "text",
                    "render_status": result.render_status,
                    "page_count": result.page_count,
                    "rendered_text": result.rendered_text,
                },
                ensure_ascii=False,
            )
        )
        return EXIT_OK
    if args.pages:
        start, end = _parse_page_range(args.pages)
        paths = renderer.rasterize_pages(path, start, end)
        print(
            json.dumps(
                {"mode": "pages", "pages": args.pages, "derived_image_paths": paths},
                ensure_ascii=False,
            )
        )
        return EXIT_OK
    print("render-pdf: specify --text or --pages N-M", file=sys.stderr)
    return EXIT_CONFIG_INVALID


def _load_owned_lease(config: Config, owner: str):
    """lease を load し owner 一致を検証（send-reply / proactive-send 共通）。OK なら
    (lease, lease_store)、NG なら None（stderr 出力済み、呼び出し側で EXIT_LEASE_CONFLICT）。
    """
    lease_store = JsonLeaseStore(config.state_dir)
    lease = lease_store.load()
    if lease is None:
        print("no active lease (acquire first)", file=sys.stderr)
        return None
    if lease.owner != owner:
        print(
            f"lease owned by {lease.owner!r}, not {owner!r} — refusing send",
            file=sys.stderr,
        )
        return None
    return lease, lease_store


def _outbound_exception_to_exit(exc: TelegramSecretaryError) -> int:
    """送信例外を exit code にマップ（send-reply / proactive-send 共通）。"""
    if isinstance(exc, (AttachmentNotFound, AttachmentTooLarge)):
        print(f"attachment error: {exc}", file=sys.stderr)
        return EXIT_CONFIG_INVALID
    if isinstance(exc, AuthFailureError):
        print(f"auth failure: {exc}", file=sys.stderr)
        return EXIT_AUTH_FAILED
    print(f"send failed: {exc}", file=sys.stderr)
    return EXIT_FETCH_FAILED


def cmd_send_reply(args: argparse.Namespace) -> int:
    config = _load_config()

    owner = _session_owner(args.owner)
    text = Path(args.text_file).read_text(encoding="utf-8")
    attachments = [OutboundAttachment(path=Path(f)) for f in (args.file or [])]
    owned = _load_owned_lease(config, owner)
    if owned is None:
        return EXIT_LEASE_CONFLICT
    lease, lease_store = owned
    offset_store = JsonOffsetStore(config.state_dir)

    with TelegramApiGateway(bot_token=config.bot_token) as gateway:
        # 送信前に typing を best-effort で出す（watch→Monitor→応答の数秒ラグの UX 緩和）
        gateway.send_chat_action(args.chat_id)
        try:
            SendReply(gateway, offset_store, lease_store).execute(
                message=OutboundMessage(
                    chat_id=args.chat_id,
                    text=text,
                    reply_to_message_id=args.reply_to,
                    attachments=attachments,
                ),
                update_id=args.update_id,
                lease=lease,
                now=utc_now(),
                max_bytes=config.outbound_max_size_bytes,
            )
        except TelegramSecretaryError as exc:
            return _outbound_exception_to_exit(exc)

    print(f"sent chat_id={args.chat_id} update_id={args.update_id}")
    return EXIT_OK


def cmd_proactive_send(args: argparse.Namespace) -> int:
    """秘書による能動発信（inbound 非依存の outbound push）。

    `cmd_send_reply` の写像から `offset_store` 構築と `--update-id` を除去したもの。
    offset は inbound 専用の既読台帳ゆえ能動送信では一切触れない（`ProactiveSend` が
    `OffsetStore` を依存に持たないことで構造的に保証）。

    outbound は inbound と違い offset の安全網を持たないため、WAL ライフサイクルをこのコマンドが
    内包する（DESIGN §3.9）: `append→push(送信前ゲート)→send→settle→push`。created_at を内部
    生成して settle のキーに使うことで、送信成功した intent をその場で done 化し、次回 redo の
    「成功送信の偽謝罪付き再送」を構造的に断つ（happy-path settle）。registry_sync 無効時は WAL を
    丸ごと素通りし、現行どおり send のみ（後方互換）。
    """
    config = _load_config()

    owner = _session_owner(args.owner)
    text = Path(args.text_file).read_text(encoding="utf-8")
    attachments = [OutboundAttachment(path=Path(f)) for f in (args.file or [])]
    owned = _load_owned_lease(config, owner)
    if owned is None:
        return EXIT_LEASE_CONFLICT
    lease, lease_store = owned

    # 送信前ゲート: outbound intent を WAL へ先行書込み + must-succeed push（registry_sync 有効時）。
    # push できなければ送信もしない＝言行一致（§3.7/§3.9）。wal_key は送信成功後の settle キー。
    ok, wal_key = run_wal_append_outbound(
        config, args.chat_id, text, [str(a.path) for a in attachments], args.reply_to
    )
    if not ok:
        return EXIT_FETCH_FAILED

    with TelegramApiGateway(bot_token=config.bot_token) as gateway:
        # 送信前に typing を best-effort で出す（send-reply と共通の UX）
        gateway.send_chat_action(args.chat_id)
        try:
            ProactiveSend(gateway, lease_store).execute(
                message=OutboundMessage(
                    chat_id=args.chat_id,
                    text=text,
                    reply_to_message_id=args.reply_to,
                    attachments=attachments,
                ),
                lease=lease,
                now=utc_now(),
                max_bytes=config.outbound_max_size_bytes,
            )
        except TelegramSecretaryError as exc:
            return _outbound_exception_to_exit(exc)

    # happy-path settle: 送信成功した outbound intent を done 化 + push（次回 redo の偽謝罪付き
    # 再送を断つ）。送信は既に成功済みゆえ best-effort（§3.9）。
    run_wal_settle_outbound(config, wal_key)

    print(f"sent chat_id={args.chat_id}")
    return EXIT_OK


def cmd_test(args: argparse.Namespace) -> int:
    config = _load_config()

    with TelegramApiGateway(bot_token=config.bot_token) as gateway:
        try:
            gateway.send(OutboundMessage(chat_id=args.chat_id, text=args.text))
        except AuthFailureError as exc:
            print(f"auth failure: {exc}", file=sys.stderr)
            return EXIT_AUTH_FAILED
        except TelegramSecretaryError as exc:
            print(f"send failed: {exc}", file=sys.stderr)
            return EXIT_FETCH_FAILED
    print(f"ping sent chat_id={args.chat_id}")
    return EXIT_OK


def cmd_registry(args: argparse.Namespace) -> int:
    """個人/タスク/知識 管理表の CRUD。args.command が管理表名（individuals/tasks/knowledge）。"""
    config = _load_config()
    return run_registry_command(config, args.command, args.registry_action, args)


def cmd_registry_sync(args: argparse.Namespace) -> int:
    """起動時に固定ブランチから管理表を fetch（registry_sync 有効時のみ、R2-3）。"""
    config = _load_config()
    return run_registry_fetch(config)


def cmd_wal_append(args: argparse.Namespace) -> int:
    """WAL に intent を pending 追記（送信前、registry_sync 有効時のみ）。"""
    return run_wal_append(_load_config(), args.kind, args)


def cmd_wal_push(args: argparse.Namespace) -> int:
    """WAL ログを commit & push（must-succeed、push 失敗は exit 非0＝送信前ゲート）。"""
    return run_wal_push(_load_config(), args)


def cmd_wal_redo(args: argparse.Namespace) -> int:
    """起動時に WAL pending を registry へ redo（registry_sync 有効時のみ）。"""
    return run_wal_redo(_load_config())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telegram-secretary")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate-config", help="env vars と設定の検証 (exit 0=OK / 2=設定欠損)")

    sub.add_parser("show-config", help="現在の設定を read-only 表示（秘匿はマスク、未設定でも exit 0）")

    p_init = sub.add_parser(
        "init-config", help="config.json を生成（決定論 I/O、対話的収集は /telegram-secretary 経由）"
    )
    p_init.add_argument(
        "--session-duration-sec",
        type=int,
        default=7200,
        help="セッション継続秒（1〜86400、default 7200=2h。config.json の記入例値）",
    )
    p_init.add_argument("--agent-name", help="秘書エージェントの人格名")
    p_init.add_argument("--private-dir", help="非公開データ・人格定義の配置先")
    p_init.add_argument(
        "--force", action="store_true", help="既存 config.json を上書きする"
    )

    p_lease = sub.add_parser("lease", help="リースの取得/更新/解放")
    p_lease.add_argument("action", choices=["acquire", "renew", "release"])
    p_lease.add_argument("--owner", help="session owner id (省略時は env か uuid 生成)")
    p_lease.add_argument("--ttl", type=int, default=300, help="TTL seconds (default 300)")

    p_poll = sub.add_parser("poll", help="getUpdates 1 サイクル")
    p_poll.add_argument("--timeout", type=int, default=30, help="long-poll timeout seconds")

    p_watch = sub.add_parser("watch", help="バックグラウンド long-poll ループ")
    p_watch.add_argument("--timeout", type=int, default=30)
    p_watch.add_argument("--owner", help="session owner id (lease renew 用、省略時は env か uuid)")
    p_watch.add_argument(
        "--max-iterations",
        type=int,
        default=0,
        help="0=無限ループ (cloud routine 常駐用), >0 はテスト用",
    )
    p_watch.add_argument(
        "--max-duration",
        type=int,
        default=0,
        help="0=無限 (既存挙動), >0 で N 秒経過後に自然終了。cloud routine の窓畳み用",
    )
    p_watch.add_argument(
        "--exit-on-message",
        action="store_true",
        help="認可済みメッセージを emit したサイクルで exit 0（D: early-exit→返信→再起動 運用）",
    )
    p_watch.add_argument(
        "--cleanup-interval",
        type=int,
        default=120,
        help="N サイクル毎に cleanup_media_dir を発火（0=無効、default 120 ≒ 1h with timeout=30s）",
    )

    p_send = sub.add_parser("send-reply", help="エージェント起草の返信を送信")
    p_send.add_argument("--chat-id", type=int, required=True)
    p_send.add_argument("--update-id", type=int, required=True)
    p_send.add_argument("--text-file", required=True)
    p_send.add_argument("--owner", help="session owner id (lease 検証用、省略時は env か uuid)")
    p_send.add_argument(
        "--file",
        action="append",
        default=[],
        help="送り返す添付ファイルパス（複数指定可、画像は sendPhoto・他は sendDocument）",
    )
    p_send.add_argument(
        "--reply-to",
        type=int,
        default=None,
        help="返信先メッセージ ID（reply threading）",
    )

    p_proactive = sub.add_parser(
        "proactive-send",
        help="秘書による能動発信（inbound 非依存の outbound push、offset 非干渉）",
    )
    p_proactive.add_argument("--chat-id", type=int, required=True)
    p_proactive.add_argument("--text-file", required=True)
    p_proactive.add_argument(
        "--owner", help="session owner id (lease 検証用、省略時は env か uuid)"
    )
    p_proactive.add_argument(
        "--file",
        action="append",
        default=[],
        help="送り返す添付ファイルパス（複数指定可、画像は sendPhoto・他は sendDocument）",
    )
    p_proactive.add_argument(
        "--reply-to",
        type=int,
        default=None,
        help="返信先メッセージ ID（reply threading）",
    )

    p_test = sub.add_parser("test", help="疎通テスト：owner chat に ping 送信")
    p_test.add_argument("--chat-id", type=int, required=True)
    p_test.add_argument("--text", default="ping from TelegramSecretary")

    sub.add_parser(
        "cleanup-media",
        help="保持期限超過の media ファイルを state_dir/media/ から削除",
    )

    p_render = sub.add_parser(
        "render-pdf",
        help="オンデマンド PDF 抽出: --text 全文テキスト / --pages N-M 個別ページ画像化",
    )
    p_render.add_argument("--path", required=True, help="対象 PDF の local_path")
    g_render = p_render.add_mutually_exclusive_group(required=True)
    g_render.add_argument(
        "--text", action="store_true", help="全ページのテキスト層を抽出"
    )
    g_render.add_argument(
        "--pages", help="画像化するページ範囲 N-M（1-indexed inclusive）"
    )

    # 管理表 CRUD（individuals / tasks / knowledge）。/telegram-secretary が全操作をラップする入口
    for _name in ("individuals", "tasks", "knowledge", "abilities"):
        p_reg = sub.add_parser(_name, help=f"{_name} 管理表の CRUD")
        p_reg.add_argument("registry_action", choices=["list", "get", "add", "remove"])
        p_reg.add_argument("--key", help="get/remove のキー（uuid または id）")
        p_reg.add_argument("--json", help="add するレコードの JSON 文字列")
        p_reg.add_argument("--json-file", dest="json_file", help="add するレコードの JSON ファイル")

    # 起動時 fetch（registry_sync 有効時、固定ブランチから最新管理表を引く。ROUTINE_PROMPT が起動時に1回叩く）
    sub.add_parser(
        "registry-sync", help="起動時に固定ブランチから管理表を fetch（R2-3、registry_sync 有効時）"
    )

    # WAL（Write-Ahead Log）: 送信前 intent 書込→push→起動時 redo（registry_sync 有効時のみ稼働）
    p_wal_append = sub.add_parser(
        "wal-append", help="WAL に intent を pending 追記（送信前、registry_sync 有効時）"
    )
    p_wal_append.add_argument(
        "--kind",
        required=True,
        choices=["individuals", "tasks", "knowledge", "abilities", "outbound"],
    )
    p_wal_append.add_argument("--json", help="intent payload の JSON 文字列")
    p_wal_append.add_argument(
        "--json-file", dest="json_file", help="intent payload の JSON ファイル"
    )

    p_wal_push = sub.add_parser(
        "wal-push", help="WAL ログを commit & push（must-succeed、失敗は exit 非0＝送信前ゲート）"
    )
    p_wal_push.add_argument("--message", help="commit メッセージ")

    sub.add_parser(
        "wal-redo", help="起動時に WAL pending を registry へ redo（registry_sync 有効時）"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "validate-config": cmd_validate_config,
        "show-config": cmd_show_config,
        "init-config": cmd_init_config,
        "lease": cmd_lease,
        "poll": cmd_poll,
        "watch": cmd_watch,
        "send-reply": cmd_send_reply,
        "proactive-send": cmd_proactive_send,
        "test": cmd_test,
        "cleanup-media": cmd_cleanup_media,
        "render-pdf": cmd_render_pdf,
        "individuals": cmd_registry,
        "tasks": cmd_registry,
        "knowledge": cmd_registry,
        "abilities": cmd_registry,
        "registry-sync": cmd_registry_sync,
        "wal-append": cmd_wal_append,
        "wal-push": cmd_wal_push,
        "wal-redo": cmd_wal_redo,
    }
    try:
        return handlers[args.command](args)
    except _ConfigInvalid:
        return EXIT_CONFIG_INVALID


if __name__ == "__main__":
    sys.exit(main())
