# adapters/mail/yagmail_adapter.py
"""
Yagmail メールアダプター

yagmailライブラリを使用してメール送信を行う。
HTMLテンプレートシステムにより一貫したスタイリングを実現。
指数バックオフによるリトライ機能を提供。
"""

from __future__ import annotations

import logging
import smtplib
import time

import yagmail

from domain.exceptions import MailError

logger = logging.getLogger('emailingessay.mail')

# 後方互換性のため再エクスポート
__all__ = ["YagmailAdapter", "MailError"]

# HTMLテンプレート名
EMAIL_TEMPLATE_NAME = "email_base.html.template"
EMAIL_FALLBACK_TEMPLATE = "email_fallback.html.template"


class YagmailAdapter:
    """Yagmail を使用したメールアダプター"""

    def __init__(self) -> None:
        """
        アダプターを初期化する。

        Configから設定を読み込む（環境変数または.envファイル経由）。

        Raises:
            MailError: 必要な設定が不足している場合
        """
        from domain.config import Config

        config = Config.load()
        errors = config.validate()
        if errors:
            raise MailError("; ".join(errors))

        self._sender = config.email.sender
        self._password = config.email.password
        self._recipient = config.email.recipient

    def _render_html(self, content: str, title: str = "") -> str:
        """
        共通HTMLテンプレートでコンテンツをラップする。

        Args:
            content: HTML本文（タグ含む）
            title: オプションのタイトル（h2タグで表示）

        Returns:
            テンプレートでラップされたHTML文字列
        """
        from frameworks.templates import load_template, render_template

        try:
            template = load_template(EMAIL_TEMPLATE_NAME)
            if title:
                inner = f'<h2 class="email-title">{title}</h2><div class="email-content">{content}</div>'
            else:
                inner = f'<div class="email-content">{content}</div>'
            return render_template(template, content=inner)
        except Exception:
            # フォールバックテンプレートを使用
            try:
                fallback_template = load_template(EMAIL_FALLBACK_TEMPLATE)
                title_block = f'<h2 style="color: #f97316;">{title}</h2>' if title else ''
                return render_template(fallback_template, title_block=title_block, content=content)
            except Exception:
                # 最終手段: 最小限のHTML
                return f"<div>{content}</div>"

    def send(self, to: str, subject: str, body: str, max_retries: int = 3) -> None:
        """
        メールを送信する（指数バックオフ付きリトライ）。

        Args:
            to: 送信先（空の場合はデフォルト受信者）
            subject: 件名
            body: 本文（HTML可）
            max_retries: 最大リトライ回数（デフォルト3回）

        Raises:
            MailError: 送信に失敗した場合
        """
        recipient = to if to else self._recipient
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                with yagmail.SMTP(self._sender, self._password) as yag:
                    yag.send(to=recipient, subject=subject, contents=body)
                print(f"Sent to: {recipient}")
                return
            except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, OSError) as e:
                # 一時的なネットワーク障害はリトライ
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # 1s, 2s, 4s
                    logger.warning(
                        f"SMTP transient error, retry {attempt + 1}/{max_retries} in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
            except smtplib.SMTPAuthenticationError as e:
                # 認証エラーはリトライしない
                raise MailError(f"Authentication failed: {e}") from e
            except Exception as e:
                # その他のエラーはリトライしない
                raise MailError(f"Failed to send email: {e}") from e

        # リトライ上限到達
        raise MailError(f"Failed after {max_retries} retries: {last_error}")

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
