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
        "-t", "--theme", default="", help="Essay theme (エッセイのテーマ)"
    )
    parser.add_argument(
        "-c",
        "--context",
        default="",
        help="Context file path (コンテキストファイルのパス)",
    )
    parser.add_argument(
        "-f",
        "--file-list",
        dest="file_list",
        default="",
        help="File list path (ファイルリストのパス)",
    )
    parser.add_argument(
        "-l",
        "--lang",
        default="auto",
        choices=["ja", "en", "auto"],
        help="Language (言語: ja, en, auto)",
    )
    parser.add_argument(
        "--name", default="", help="Custom task name (カスタムタスク名)"
    )


def create_parser() -> argparse.ArgumentParser:
    """
    メインパーサーを作成する。

    サブコマンド構造:
    - test: テストメール送信
    - send: カスタムメール送信
    - wait: 一回限りのエッセイ配信
        - <time>: 指定時刻に待機
        - list: アクティブな待機プロセス一覧
    - replies: 返信の取り込み
        - fetch: 受信箱から返信を取り込む
        - list: 取り込み済み返信の一覧
    - ledger: 送信台帳
        - import-legacy: 過去の本文を台帳へ遡及移行する
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
  python main.py send "Note" "Body" --to-self  # Send a note to the AI's own address
  python main.py send --subject-file s.txt --body-file b.txt  # Send from files
  python main.py wait 09:30 -t "morning"       # Schedule one-time essay
  python main.py wait list                     # List active waiting processes
  python main.py replies fetch                 # Ingest replies from the inbox
  python main.py replies list                  # List ingested replies
  python main.py ledger import-legacy --dry-run  # Preview the legacy import
  python main.py ledger import-legacy          # Import past essays into the ledger
  python main.py schedule daily 09:00          # Add daily schedule
  python main.py schedule weekly monday 10:00  # Add weekly schedule
  python main.py schedule monthly last_fri 15:00  # Add monthly schedule
  python main.py schedule list                 # List all schedules
  python main.py schedule remove task_name     # Remove a schedule
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # -------------------------------------------------------------------------
    # test コマンド
    # -------------------------------------------------------------------------
    subparsers.add_parser("test", help="Send test email (テストメール送信)")

    # -------------------------------------------------------------------------
    # send コマンド
    # -------------------------------------------------------------------------
    send_parser = subparsers.add_parser(
        "send", help="Send custom email (カスタムメール送信)"
    )
    # 件名・本文はそれぞれ「位置引数」か「ファイル」のどちらか一方で渡す。
    # 相互排他をパーサに持たせるため、位置引数を nargs="?" にして排他グループへ入れる
    # （handler 側の判定では「同時指定をパーサがエラーにする」を満たせない）。
    # ファイル経由は Windows のシェル引数に載らない複数段落の日本語本文のための経路。
    subject_group = send_parser.add_mutually_exclusive_group()
    subject_group.add_argument(
        "subject", nargs="?", default="", help="Email subject (メールの件名)"
    )
    subject_group.add_argument(
        "--subject-file",
        dest="subject_file",
        default="",
        help="Read the subject from a file (件名をファイルから読む)",
    )
    body_group = send_parser.add_mutually_exclusive_group()
    body_group.add_argument(
        "body", nargs="?", default="", help="Email body (メールの本文)"
    )
    body_group.add_argument(
        "--body-file",
        dest="body_file",
        default="",
        help="Read the body from a file (本文をファイルから読む)",
    )
    send_parser.add_argument(
        "--to-self",
        action="store_true",
        help="Send to the AI's own address (自分宛に送る — 書き置き用)",
    )

    # -------------------------------------------------------------------------
    # wait コマンド
    # -------------------------------------------------------------------------
    wait_parser = subparsers.add_parser(
        "wait",
        help="Schedule one-time essay or list waiters (一回限りのエッセイ配信 / 待機一覧)",
    )
    wait_parser.add_argument(
        "time",
        help="Target time (HH:MM or YYYY-MM-DD HH:MM) or 'list' to show active waiters",
    )
    add_common_options(wait_parser)

    # -------------------------------------------------------------------------
    # replies コマンド（ネストされたサブパーサー）
    # -------------------------------------------------------------------------
    replies_parser = subparsers.add_parser(
        "replies", help="Manage essay replies (返信の取り込み)"
    )
    replies_subs = replies_parser.add_subparsers(
        dest="replies_cmd", help="Replies sub-commands"
    )
    replies_subs.add_parser(
        "fetch", help="Fetch replies from the inbox (受信箱から返信を取り込む)"
    )
    replies_subs.add_parser(
        "list", help="List ingested replies (取り込み済み返信の一覧)"
    )

    # -------------------------------------------------------------------------
    # ledger コマンド（ネストされたサブパーサー）
    # -------------------------------------------------------------------------
    ledger_parser = subparsers.add_parser(
        "ledger", help="Manage the sent ledger (送信台帳)"
    )
    ledger_subs = ledger_parser.add_subparsers(
        dest="ledger_cmd", help="Ledger sub-commands"
    )
    import_legacy_parser = ledger_subs.add_parser(
        "import-legacy",
        help="Import past essays into the ledger (過去の本文を台帳へ遡及移行)",
    )
    import_legacy_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Show the plan without writing anything (何も書かずに計画を出す)",
    )

    # -------------------------------------------------------------------------
    # schedule コマンド（ネストされたサブパーサー）
    # -------------------------------------------------------------------------
    schedule_parser = subparsers.add_parser(
        "schedule", help="Manage recurring schedules (定期配信管理)"
    )
    schedule_subs = schedule_parser.add_subparsers(
        dest="schedule_cmd", help="Schedule sub-commands"
    )

    # schedule list
    schedule_subs.add_parser("list", help="List all schedules (スケジュール一覧)")

    # schedule remove
    remove_parser = schedule_subs.add_parser(
        "remove", help="Remove a schedule (スケジュール削除)"
    )
    remove_parser.add_argument(
        "name", help="Schedule name to remove (削除するスケジュール名)"
    )

    # schedule daily
    daily_parser = schedule_subs.add_parser(
        "daily", help="Add daily schedule (日次スケジュール追加)"
    )
    daily_parser.add_argument("time", help="Time (HH:MM)")
    add_common_options(daily_parser)

    # schedule weekly
    weekly_parser = schedule_subs.add_parser(
        "weekly", help="Add weekly schedule (週次スケジュール追加)"
    )
    weekly_parser.add_argument("weekday", help="Day of week (monday, tuesday, ...)")
    weekly_parser.add_argument("time", help="Time (HH:MM)")
    add_common_options(weekly_parser)

    # schedule monthly
    monthly_parser = schedule_subs.add_parser(
        "monthly", help="Add monthly schedule (月次スケジュール追加)"
    )
    monthly_parser.add_argument(
        "day_spec", help="Day specification (15, 2nd_mon, last_fri, last_day)"
    )
    monthly_parser.add_argument("time", help="Time (HH:MM)")
    add_common_options(monthly_parser)

    return parser


if __name__ == "__main__":
    # デバッグ用
    parser = create_parser()
    args = parser.parse_args()
    print(f"Parsed args: {args}")
