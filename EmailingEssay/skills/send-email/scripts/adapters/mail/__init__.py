# adapters/mail/__init__.py
"""
メールアダプター

メール送信の実装を提供する。
"""

from .imap_inbox import ImapInboxAdapter
from .ledger_recording_mail import LedgerRecordingMail
from .yagmail_adapter import MailError, YagmailAdapter

__all__ = ["ImapInboxAdapter", "LedgerRecordingMail", "MailError", "YagmailAdapter"]
