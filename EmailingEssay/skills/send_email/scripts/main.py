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
  python main.py wait list                               # List active waiters
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

from adapters.cli import create_parser, dispatch
from domain.exceptions import EmailingEssayError
from frameworks.logging_config import configure_logging, get_logger

# ロギング初期化
configure_logging()
logger = get_logger("main")


def main() -> int:
    """メインエントリーポイント"""
    logger.debug("Starting main()")
    parser = create_parser()
    args = parser.parse_args()

    try:
        result = dispatch(args)
        if result == -1:
            # コマンド未指定
            parser.print_help()
            return 0
        return result

    except EmailingEssayError as e:
        # カスタム例外（MailError, SchedulerError, ValidationError等）を統一処理
        logger.error(f"{e.__class__.__name__}: {e}")
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        print(f"Invalid argument: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return 1
    except PermissionError as e:
        print(f"Permission denied: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Unexpected error ({type(e).__name__}): {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
