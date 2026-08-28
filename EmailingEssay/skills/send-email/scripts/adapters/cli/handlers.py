# adapters/cli/handlers.py
"""
コマンドハンドラレジストリ

main.pyの条件分岐ロジックをハンドラ関数に分離。
保守性と拡張性を向上させる。
"""

from __future__ import annotations

from argparse import Namespace
from collections.abc import Callable
from typing import TYPE_CHECKING

from usecases.factories import (
    create_import_legacy_usecase,
    create_ingest_replies_usecase,
    create_schedule_usecase,
    create_wait_usecase,
    get_ledger,
    get_mail_adapter,
)

from .decorators import validate_config

if TYPE_CHECKING:
    from usecases.import_legacy import LegacyPlan

# ハンドラ型: argsを受け取り、終了コードを返す
Handler = Callable[[Namespace], int]


# =============================================================================
# メール系ハンドラ
# =============================================================================


@validate_config
def handle_test(args: Namespace) -> int:
    """テストメール送信"""
    mail = get_mail_adapter()
    mail.test()
    return 0


@validate_config
def handle_send(args: Namespace) -> int:
    """カスタムメール送信"""
    mail = get_mail_adapter()
    mail.send_custom(args.subject, args.body)
    return 0


# =============================================================================
# 待機ハンドラ
# =============================================================================


def handle_wait(args: Namespace) -> int:
    """待機コマンド（list または spawn）"""
    waiter = create_wait_usecase()

    if args.time == "list":
        waiters = waiter.list_waiters()
        if not waiters:
            print("No active waiting processes.")
            return 0
        print(f"Active waiting processes: {len(waiters)}")
        print("-" * 60)
        for w in waiters:
            pid = w.get("pid", "?")
            target = w.get("target_time", "?")
            theme = w.get("theme", "") or "(no theme)"
            registered = w.get("registered_at", "?")
            print(f"  PID: {pid}")
            print(f"    Target: {target}")
            print(f"    Theme:  {theme}")
            print(f"    Registered: {registered}")
            print()
        return 0

    waiter.spawn(
        target_time=args.time,
        theme=args.theme,
        context=args.context,
        file_list=args.file_list,
        lang=args.lang,
    )
    return 0


# =============================================================================
# 返信サブハンドラ
# =============================================================================


@validate_config
def _handle_replies_fetch(args: Namespace) -> int:
    """受信箱から返信を取り込む"""
    usecase = create_ingest_replies_usecase()
    ingested = usecase.fetch()
    print(f"Ingested replies: {len(ingested)}")
    return 0


def _handle_replies_list(args: Namespace) -> int:
    """
    取り込み済み返信の一覧（本文は出さない）。

    本文は外部入力であり、端末やログへ素で流す経路を作らない
    （読むときは essay_replies.jsonl を data として開く — ops-rules 7）。
    台帳を読むだけなので資格情報を要さない。
    """
    replies = get_ledger().load_replies()
    if not replies:
        print("No replies ingested yet.")
        return 0

    print(f"Ingested replies: {len(replies)}")
    print("-" * 60)
    for r in replies:
        print(f"  Message-ID: {r.message_id}")
        print(f"    In-Reply-To: {r.in_reply_to}")
        print(f"    From:        {r.sender}")
        print(f"    Received:    {r.received_at}")
        print()
    return 0


# 返信サブコマンドのレジストリ
REPLIES_HANDLERS: dict[str, Handler] = {
    "fetch": _handle_replies_fetch,
    "list": _handle_replies_list,
}


def handle_replies(args: Namespace) -> int:
    """返信コマンド（サブコマンドにディスパッチ）"""
    handler = REPLIES_HANDLERS.get(args.replies_cmd)
    if not handler:
        print(f"Unknown replies subcommand: {args.replies_cmd}")
        return 1
    return handler(args)


# =============================================================================
# 台帳サブハンドラ
# =============================================================================


def _print_legacy_plan(plan: LegacyPlan) -> None:
    """
    移行計画を検品できる形で出す。

    件数だけでは取り違えを検出できない（本文を 1 本入れ替えても件数は同じ）。
    どの本文にどの件名がどの出所から付くのかを 1 件ずつ並べる。
    """
    print(f"Import candidates: {len(plan.items)}")
    print("-" * 60)
    for item in plan.items:
        print(f"  {item.sent_at}  {item.body_file}")
        print(f"    subject: {item.subject}")
        print(f"    source:  {item.subject_source}")
        print(f"    id:      {item.message_id}")
    print()
    print(f"Excluded: {len(plan.skipped)}")
    print("-" * 60)
    for skip in plan.skipped:
        print(f"  {skip.body_file} — {skip.reason}")
    print()
    if plan.warnings:
        print(f"Warnings: {len(plan.warnings)}")
        for warning in plan.warnings:
            print(f"  {warning}")
        print()


@validate_config
def _handle_ledger_import_legacy(args: Namespace) -> int:
    """
    過去の本文を台帳へ遡及移行する。

    --dry-run は計画を出すだけで何も書かない（plan() は書き込み経路を持たない）。
    移行元は読むだけ——削除も改変もしない。
    """
    usecase = create_import_legacy_usecase()

    if args.dry_run:
        print("Dry run: nothing is written.")
        _print_legacy_plan(usecase.plan())
        return 0

    _print_legacy_plan(usecase.plan())
    records = usecase.execute()
    print(f"Imported: {len(records)}")
    return 0


# 台帳サブコマンドのレジストリ
LEDGER_HANDLERS: dict[str, Handler] = {
    "import-legacy": _handle_ledger_import_legacy,
}


def handle_ledger(args: Namespace) -> int:
    """台帳コマンド（サブコマンドにディスパッチ）"""
    handler = LEDGER_HANDLERS.get(args.ledger_cmd)
    if not handler:
        print(f"Unknown ledger subcommand: {args.ledger_cmd}")
        return 1
    return handler(args)


# =============================================================================
# スケジュールサブハンドラ
# =============================================================================


def _handle_schedule_list(args: Namespace) -> int:
    """スケジュール一覧"""
    usecase = create_schedule_usecase()
    usecase.list()
    return 0


def _handle_schedule_remove(args: Namespace) -> int:
    """スケジュール削除"""
    usecase = create_schedule_usecase()
    usecase.remove(args.name)
    return 0


def _handle_schedule_add(args: Namespace, frequency: str) -> int:
    """ジェネリックスケジュール追加ハンドラ"""
    usecase = create_schedule_usecase()
    usecase.add(
        frequency=frequency,
        time_spec=args.time,
        weekday=getattr(args, "weekday", ""),
        theme=args.theme,
        context_file=args.context,
        file_list=args.file_list,
        lang=args.lang,
        name=args.name,
        day_spec=getattr(args, "day_spec", ""),
    )
    return 0


# スケジュールサブコマンドのレジストリ
SCHEDULE_HANDLERS: dict[str, Handler] = {
    "list": _handle_schedule_list,
    "remove": _handle_schedule_remove,
    "daily": lambda args: _handle_schedule_add(args, "daily"),
    "weekly": lambda args: _handle_schedule_add(args, "weekly"),
    "monthly": lambda args: _handle_schedule_add(args, "monthly"),
}


def handle_schedule(args: Namespace) -> int:
    """スケジュールコマンド（サブコマンドにディスパッチ）"""
    handler = SCHEDULE_HANDLERS.get(args.schedule_cmd)
    if not handler:
        print(f"Unknown schedule subcommand: {args.schedule_cmd}")
        return 1
    return handler(args)


# =============================================================================
# メインハンドラレジストリ
# =============================================================================

HANDLERS: dict[str, Handler] = {
    "test": handle_test,
    "send": handle_send,
    "wait": handle_wait,
    "replies": handle_replies,
    "ledger": handle_ledger,
    "schedule": handle_schedule,
}


def dispatch(args: Namespace) -> int:
    """
    コマンドをディスパッチする。

    Args:
        args: パース済み引数

    Returns:
        終了コード（-1: コマンド未指定、0: 成功、1: エラー）
    """
    if not args.command:
        return -1  # ヘルプ表示シグナル

    handler = HANDLERS.get(args.command)
    if not handler:
        print(f"Unknown command: {args.command}")
        return 1

    return handler(args)


__all__ = ["HANDLERS", "LEDGER_HANDLERS", "REPLIES_HANDLERS", "dispatch"]
