# adapters/mail/__init__.py
"""
メールアダプター

メール送信の実装を提供する。
"""

from .yagmail_adapter import MailError, YagmailAdapter

__all__ = ["MailError", "YagmailAdapter"]
