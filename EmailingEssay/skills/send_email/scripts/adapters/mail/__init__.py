# adapters/mail/__init__.py
"""
メールアダプター

メール送信の実装を提供する。
"""
from .yagmail_adapter import YagmailAdapter, MailError

__all__ = ["YagmailAdapter", "MailError"]
