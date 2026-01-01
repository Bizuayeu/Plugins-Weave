# adapters/cli/handlers.py
"""
CLI コマンドハンドラ

各CLIコマンドのハンドラ関数を定義する。
ハンドラはUse Casesを呼び出すだけで、ビジネスロジックは含まない。
"""
import argparse
from typing import Any, Optional

# Portインターフェースは呼び出し時に注入される


def handle_test(
    args: argparse.Namespace,
    *,
    mail_port: Any
) -> None:
    """
    'test' コマンドのハンドラ

    テストメールを送信する。

    Args:
        args: パースされた引数
        mail_port: MailPort実装
    """
    mail_port.test()


def handle_send(
    args: argparse.Namespace,
    *,
    mail_port: Any
) -> None:
    """
    'send' コマンドのハンドラ

    カスタムメールを送信する。

    Args:
        args: パースされた引数（subject, body）
        mail_port: MailPort実装
    """
    mail_port.send(
        to="",  # デフォルト送信先はPort側で管理
        subject=args.subject,
        body=args.body
    )


def handle_wait(
    args: argparse.Namespace,
    *,
    waiter_port: Any
) -> None:
    """
    'wait' コマンドのハンドラ

    一回限りのエッセイ配信を設定する。

    Args:
        args: パースされた引数（time, theme, context, file_list, lang）
        waiter_port: WaiterPort実装
    """
    waiter_port.spawn(
        target_time=args.time,
        theme=args.theme,
        context=args.context,
        file_list=args.file_list,
        lang=args.lang
    )


def handle_schedule_list(
    args: argparse.Namespace,
    *,
    scheduler_port: Any
) -> None:
    """
    'schedule list' コマンドのハンドラ

    スケジュール一覧を表示する。

    Args:
        args: パースされた引数
        scheduler_port: SchedulerPort実装
    """
    schedules = scheduler_port.list()
    if not schedules:
        print("No schedules registered.")
    else:
        for schedule in schedules:
            print(f"  - {schedule}")


def handle_schedule_remove(
    args: argparse.Namespace,
    *,
    scheduler_port: Any
) -> None:
    """
    'schedule remove' コマンドのハンドラ

    指定したスケジュールを削除する。

    Args:
        args: パースされた引数（name）
        scheduler_port: SchedulerPort実装
    """
    scheduler_port.remove(args.name)


def handle_schedule_daily(
    args: argparse.Namespace,
    *,
    scheduler_port: Any
) -> None:
    """
    'schedule daily' コマンドのハンドラ

    日次スケジュールを追加する。

    Args:
        args: パースされた引数（time, theme, context, file_list, lang, name）
        scheduler_port: SchedulerPort実装
    """
    task_name = args.name if args.name else f"daily_{args.time.replace(':', '')}"

    scheduler_port.add(
        task_name=task_name,
        command="",  # Scheduler側で構築
        frequency="daily",
        time=args.time,
        theme=args.theme,
        context=args.context,
        file_list=args.file_list,
        lang=args.lang
    )


def handle_schedule_weekly(
    args: argparse.Namespace,
    *,
    scheduler_port: Any
) -> None:
    """
    'schedule weekly' コマンドのハンドラ

    週次スケジュールを追加する。

    Args:
        args: パースされた引数（weekday, time, theme, context, file_list, lang, name）
        scheduler_port: SchedulerPort実装
    """
    task_name = args.name if args.name else f"weekly_{args.weekday}_{args.time.replace(':', '')}"

    scheduler_port.add(
        task_name=task_name,
        command="",
        frequency="weekly",
        time=args.time,
        weekday=args.weekday,
        theme=args.theme,
        context=args.context,
        file_list=args.file_list,
        lang=args.lang
    )


def handle_schedule_monthly(
    args: argparse.Namespace,
    *,
    scheduler_port: Any
) -> None:
    """
    'schedule monthly' コマンドのハンドラ

    月次スケジュールを追加する。

    Args:
        args: パースされた引数（day_spec, time, theme, context, file_list, lang, name）
        scheduler_port: SchedulerPort実装
    """
    task_name = args.name if args.name else f"monthly_{args.day_spec}_{args.time.replace(':', '')}"

    scheduler_port.add(
        task_name=task_name,
        command="",
        frequency="monthly",
        time=args.time,
        day_spec=args.day_spec,
        theme=args.theme,
        context=args.context,
        file_list=args.file_list,
        lang=args.lang
    )
