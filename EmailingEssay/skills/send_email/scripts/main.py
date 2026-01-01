#!/usr/bin/env python3
"""
Essay Mail - EmailingEssay email sending skill
===============================================

Clean Architecture によるエントリーポイント。
モジュール化された構造で保守性とテスト性を向上。

Usage:
  python main.py test                                    # Test send
  python main.py send "Subject" "Body"                   # Custom send
  python main.py wait "22:00" -t "theme"                 # Today/tomorrow
  python main.py wait "22:00" -t "theme" -l ja           # With language
  python main.py wait "2025-01-05 22:00" -t "theme"      # Specific date
  python main.py schedule daily 22:00 -t "theme"         # Daily schedule
  python main.py schedule weekly monday 09:00            # Weekly schedule
  python main.py schedule monthly 15 09:00 -t "theme"    # Monthly (day)
  python main.py schedule monthly 2nd_mon 09:00          # Monthly (Nth weekday)
  python main.py schedule monthly last_fri 17:00         # Monthly (last weekday)
  python main.py schedule monthly last_day 22:00         # Monthly (last day)
  python main.py schedule list                           # List schedules
  python main.py schedule remove "name"                  # Remove schedule

Environment variables:
  ESSAY_APP_PASSWORD    - Gmail app password (required)
  ESSAY_SENDER_EMAIL    - Sender email address (required)
  ESSAY_RECIPIENT_EMAIL - Recipient email address (required)
"""
from __future__ import annotations

import sys

# Windows cp932 encoding workaround
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from adapters.cli.parser import create_parser
from adapters.mail import YagmailAdapter, MailError
from usecases.wait_essay import WaitEssayUseCase
from usecases.schedule_essay import schedule_add, schedule_list, schedule_remove


def main():
    """メインエントリーポイント"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "test":
            # 新しいモジュールを使用
            mail = YagmailAdapter()
            mail.test()

        elif args.command == "send":
            # 新しいモジュールを使用
            mail = YagmailAdapter()
            mail.send_custom(args.subject, args.body)

        elif args.command == "wait":
            # 新しいモジュールを使用
            waiter = WaitEssayUseCase()
            waiter.spawn(
                target_time=args.time,
                theme=args.theme,
                context=args.context,
                file_list=args.file_list,
                lang=args.lang
            )

        elif args.command == "schedule":
            if args.schedule_cmd == "list":
                schedule_list()

            elif args.schedule_cmd == "remove":
                schedule_remove(args.name)

            elif args.schedule_cmd == "daily":
                schedule_add(
                    frequency="daily",
                    time_spec=args.time,
                    weekday="",
                    theme=args.theme,
                    context_file=args.context,
                    file_list=args.file_list,
                    lang=args.lang,
                    name=args.name
                )

            elif args.schedule_cmd == "weekly":
                schedule_add(
                    frequency="weekly",
                    time_spec=args.time,
                    weekday=args.weekday,
                    theme=args.theme,
                    context_file=args.context,
                    file_list=args.file_list,
                    lang=args.lang,
                    name=args.name
                )

            elif args.schedule_cmd == "monthly":
                schedule_add(
                    frequency="monthly",
                    time_spec=args.time,
                    weekday="",
                    theme=args.theme,
                    context_file=args.context,
                    file_list=args.file_list,
                    lang=args.lang,
                    name=args.name,
                    day_spec=args.day_spec
                )

            else:
                print(f"Unknown schedule subcommand: {args.schedule_cmd}")
                return 1

        else:
            print(f"Unknown command: {args.command}")
            return 1

        return 0

    except MailError as e:
        print(f"Mail error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
