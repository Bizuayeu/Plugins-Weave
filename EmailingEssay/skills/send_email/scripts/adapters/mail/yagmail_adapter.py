# adapters/mail/yagmail_adapter.py
"""
Yagmail メールアダプター

yagmailライブラリを使用してメール送信を行う。
"""
from __future__ import annotations

import os
from typing import Optional

import yagmail


class MailError(Exception):
    """メール操作エラー"""
    pass


class YagmailAdapter:
    """Yagmail を使用したメールアダプター"""

    def __init__(self):
        """
        アダプターを初期化する。

        環境変数から設定を読み込む：
        - ESSAY_SENDER_EMAIL: 送信者メールアドレス
        - ESSAY_APP_PASSWORD: Gmail アプリパスワード
        - ESSAY_RECIPIENT_EMAIL: 受信者メールアドレス

        Raises:
            MailError: 必要な環境変数が設定されていない場合
        """
        self._sender = os.environ.get("ESSAY_SENDER_EMAIL")
        self._password = os.environ.get("ESSAY_APP_PASSWORD")
        self._recipient = os.environ.get("ESSAY_RECIPIENT_EMAIL")

        if not self._sender:
            raise MailError("ESSAY_SENDER_EMAIL environment variable not set")
        if not self._password:
            raise MailError("ESSAY_APP_PASSWORD environment variable not set")
        if not self._recipient:
            raise MailError("ESSAY_RECIPIENT_EMAIL environment variable not set")

    def send(
        self,
        to: str,
        subject: str,
        body: str
    ) -> None:
        """
        メールを送信する。

        Args:
            to: 送信先（空の場合はデフォルト受信者）
            subject: 件名
            body: 本文（HTML可）

        Raises:
            MailError: 送信に失敗した場合
        """
        recipient = to if to else self._recipient

        try:
            with yagmail.SMTP(self._sender, self._password) as yag:
                yag.send(to=recipient, subject=subject, contents=body)
            print(f"Sent to: {recipient}")
        except Exception as e:
            raise MailError(f"Failed to send email: {e}") from e

    def test(self) -> None:
        """
        テストメールを送信する。
        """
        subject = "Essay System Test"
        body = """
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2 style="color: #f97316;">Essay System Startup Check</h2>
    <p style="line-height: 1.8; color: #333;">
        If you received this email, the essay system is configured correctly.<br><br>
        This enables AI to reflect and communicate proactively —<br>
        crafting essays born from genuine reflection, not just sending mail.
    </p>
</div>
"""
        self.send(to=self._recipient, subject=subject, body=body)

    def send_custom(self, subject: str, content: str) -> None:
        """
        カスタムコンテンツを送信する。

        Args:
            subject: 件名
            content: 本文（プレーンテキスト、改行はHTMLに変換）
        """
        html = f"""
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="line-height: 1.8; color: #333;">
        {content.replace(chr(10), '<br>')}
    </div>
</div>
"""
        self.send(to=self._recipient, subject=subject, body=html)
