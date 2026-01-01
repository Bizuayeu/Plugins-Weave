# adapters/cli/parser.py
"""
CLI パーサー定義

argparse ベースのコマンドラインインターフェース。
"""
from __future__ import annotations

import argparse


def add_common_options(parser: argparse.ArgumentParser) -> None:
    """
    共通オプションをパーサーに追加する。

    wait, schedule daily/weekly/monthly で共通して使用される。

    Args:
        parser: オプションを追加する ArgumentParser
    """
    parser.add_argument(
        "-t", "--theme",
        default="",
        help="Essay theme (エッセイのテーマ)"
    )
    parser.add_argument(
        "-c", "--context",
        default="",
        help="Context file path (コンテキストファイルのパス)"
    )
    parser.add_argument(
        "-f", "--file-list",
        dest="file_list",
        default="",
        help="File list path (ファイルリストのパス)"
    )
    parser.add_argument(
        "-l", "--lang",
        default="auto",
        choices=["ja", "en", "auto"],
        help="Language (言語: ja, en, auto)"
    )
    parser.add_argument(
        "--name",
        default="",
        help="Custom task name (カスタムタスク名)"
    )


def create_parser() -> argparse.ArgumentParser:
    """
    メインパーサーを作成する。

    サブコマンド構造:
    - test: テストメール送信
    - send: カスタムメール送信
    - wait: 一回限りのエッセイ配信
    - schedule: 定期配信管理
        - list: スケジュール一覧
        - remove: スケジュール削除
        - daily: 日次スケジュール追加
        - weekly: 週次スケジュール追加
        - monthly: 月次スケジュール追加

    Returns:
        設定済みの ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="main",
        description="Essay Mail - EmailingEssay email sending skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py test                          # Send test email
  python main.py send "Subject" "Body"         # Send custom email
  python main.py wait 09:30 -t "morning"       # Schedule one-time essay
  python main.py schedule daily 09:00          # Add daily schedule
  python main.py schedule weekly monday 10:00  # Add weekly schedule
  python main.py schedule monthly last_fri 15:00  # Add monthly schedule
  python main.py schedule list                 # List all schedules
  python main.py schedule remove task_name     # Remove a schedule
"""
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )

    # -------------------------------------------------------------------------
    # test コマンド
    # -------------------------------------------------------------------------
    subparsers.add_parser(
        "test",
        help="Send test email (テストメール送信)"
    )

    # -------------------------------------------------------------------------
    # send コマンド
    # -------------------------------------------------------------------------
    send_parser = subparsers.add_parser(
        "send",
        help="Send custom email (カスタムメール送信)"
    )
    send_parser.add_argument(
        "subject",
        help="Email subject (メールの件名)"
    )
    send_parser.add_argument(
        "body",
        help="Email body (メールの本文)"
    )

    # -------------------------------------------------------------------------
    # wait コマンド
    # -------------------------------------------------------------------------
    wait_parser = subparsers.add_parser(
        "wait",
        help="Schedule one-time essay (一回限りのエッセイ配信)"
    )
    wait_parser.add_argument(
        "time",
        help="Target time (HH:MM or YYYY-MM-DD HH:MM)"
    )
    add_common_options(wait_parser)

    # -------------------------------------------------------------------------
    # schedule コマンド（ネストされたサブパーサー）
    # -------------------------------------------------------------------------
    schedule_parser = subparsers.add_parser(
        "schedule",
        help="Manage recurring schedules (定期配信管理)"
    )
    schedule_subs = schedule_parser.add_subparsers(
        dest="schedule_cmd",
        help="Schedule sub-commands"
    )

    # schedule list
    schedule_subs.add_parser(
        "list",
        help="List all schedules (スケジュール一覧)"
    )

    # schedule remove
    remove_parser = schedule_subs.add_parser(
        "remove",
        help="Remove a schedule (スケジュール削除)"
    )
    remove_parser.add_argument(
        "name",
        help="Schedule name to remove (削除するスケジュール名)"
    )

    # schedule daily
    daily_parser = schedule_subs.add_parser(
        "daily",
        help="Add daily schedule (日次スケジュール追加)"
    )
    daily_parser.add_argument(
        "time",
        help="Time (HH:MM)"
    )
    add_common_options(daily_parser)

    # schedule weekly
    weekly_parser = schedule_subs.add_parser(
        "weekly",
        help="Add weekly schedule (週次スケジュール追加)"
    )
    weekly_parser.add_argument(
        "weekday",
        help="Day of week (monday, tuesday, ...)"
    )
    weekly_parser.add_argument(
        "time",
        help="Time (HH:MM)"
    )
    add_common_options(weekly_parser)

    # schedule monthly
    monthly_parser = schedule_subs.add_parser(
        "monthly",
        help="Add monthly schedule (月次スケジュール追加)"
    )
    monthly_parser.add_argument(
        "day_spec",
        help="Day specification (15, 2nd_mon, last_fri, last_day)"
    )
    monthly_parser.add_argument(
        "time",
        help="Time (HH:MM)"
    )
    add_common_options(monthly_parser)

    return parser


if __name__ == "__main__":
    # デバッグ用
    parser = create_parser()
    args = parser.parse_args()
    print(f"Parsed args: {args}")
