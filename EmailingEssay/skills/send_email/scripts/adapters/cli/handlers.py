# adapters/cli/handlers.py
"""
コマンドハンドラレジストリ

main.pyの条件分岐ロジックをハンドラ関数に分離。
保守性と拡張性を向上させる。
"""
from __future__ import annotations

from argparse import Namespace
from typing import Callable

from usecases.factories import (
    get_mail_adapter,
    validate_environment,
    schedule_add,
    schedule_list,
    schedule_remove,
    wait_list,
    create_wait_usecase,
)

# ハンドラ型: argsを受け取り、終了コードを返す
Handler = Callable[[Namespace], int]


# =============================================================================
# メール系ハンドラ
# =============================================================================

def handle_test(args: Namespace) -> int:
    """テストメール送信"""
    env_errors = validate_environment()
    if env_errors:
        for err in env_errors:
            print(f"Error: {err}")
        return 1

    mail = get_mail_adapter()
    mail.test()
    return 0


def handle_send(args: Namespace) -> int:
    """カスタムメール送信"""
    env_errors = validate_environment()
    if env_errors:
        for err in env_errors:
            print(f"Error: {err}")
        return 1

    mail = get_mail_adapter()
    mail.send_custom(args.subject, args.body)
    return 0


# =============================================================================
# 待機ハンドラ
# =============================================================================

def handle_wait(args: Namespace) -> int:
    """待機コマンド（list または spawn）"""
    if args.time == "list":
        wait_list()
        return 0

    waiter = create_wait_usecase()
    waiter.spawn(
        target_time=args.time,
        theme=args.theme,
        context=args.context,
        file_list=args.file_list,
        lang=args.lang
    )
    return 0


# =============================================================================
# スケジュールサブハンドラ
# =============================================================================

def _handle_schedule_list(args: Namespace) -> int:
    """スケジュール一覧"""
    schedule_list()
    return 0


def _handle_schedule_remove(args: Namespace) -> int:
    """スケジュール削除"""
    schedule_remove(args.name)
    return 0


def _handle_schedule_add(args: Namespace, frequency: str) -> int:
    """ジェネリックスケジュール追加ハンドラ"""
    schedule_add(
        frequency=frequency,
        time_spec=args.time,
        weekday=getattr(args, 'weekday', ''),
        theme=args.theme,
        context_file=args.context,
        file_list=args.file_list,
        lang=args.lang,
        name=args.name,
        day_spec=getattr(args, 'day_spec', '')
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


__all__ = ["dispatch", "HANDLERS"]
