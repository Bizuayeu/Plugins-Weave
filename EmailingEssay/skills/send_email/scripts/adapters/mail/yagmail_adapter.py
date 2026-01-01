# adapters/mail/yagmail_adapter.py
"""
Yagmail メールアダプター

yagmailライブラリを使用してメール送信を行う。
HTMLテンプレートシステムにより一貫したスタイリングを実現。
MailError は domain.exceptions に移動済み。
"""
from __future__ import annotations

import os

import yagmail

from domain.exceptions import MailError

# 後方互換性のため再エクスポート
__all__ = ["YagmailAdapter", "MailError"]

# HTMLテンプレート名
EMAIL_TEMPLATE_NAME = "email_base.html.template"


class YagmailAdapter:
    """Yagmail を使用したメールアダプター"""

    def __init__(self) -> None:
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

    def _render_html(self, content: str, title: str = "") -> str:
        """
        共通HTMLテンプレートでコンテンツをラップする。

        Args:
            content: HTML本文（タグ含む）
            title: オプションのタイトル（h2タグで表示）

        Returns:
            テンプレートでラップされたHTML文字列
        """
        try:
            from frameworks.templates import load_template, render_template
            template = load_template(EMAIL_TEMPLATE_NAME)
            if title:
                inner = f'<h2 class="email-title">{title}</h2><div class="email-content">{content}</div>'
            else:
                inner = f'<div class="email-content">{content}</div>'
            return render_template(template, content=inner)
        except Exception:
            # テンプレート読み込み失敗時はフォールバック（インラインCSS）
            fallback = f"""
<div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    {f'<h2 style="color: #f97316;">{title}</h2>' if title else ''}
    <div style="line-height: 1.8; color: #333;">
        {content}
    </div>
</div>
"""
            return fallback

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
        content = """
<p>
    If you received this email, the essay system is configured correctly.
</p>
<p>
    This enables AI to reflect and communicate proactively —<br>
    crafting essays born from genuine reflection, not just sending mail.
</p>
"""
        body = self._render_html(content, title="Essay System Startup Check")
        self.send(to=self._recipient, subject=subject, body=body)

    def send_custom(self, subject: str, content: str) -> None:
        """
        カスタムコンテンツを送信する。

        Args:
            subject: 件名
            content: 本文（プレーンテキスト、改行はHTMLに変換）
        """
        html_content = f"<p>{content.replace(chr(10), '</p><p>')}</p>"
        body = self._render_html(html_content)
        self.send(to=self._recipient, subject=subject, body=body)
