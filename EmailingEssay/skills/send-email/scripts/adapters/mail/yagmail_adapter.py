# adapters/mail/yagmail_adapter.py
"""
Yagmail メールアダプター

yagmailライブラリを使用してメール送信を行う。
HTMLテンプレートシステムにより一貫したスタイリングを実現。
指数バックオフによるリトライ機能を提供。
"""

from __future__ import annotations

import html
import re
import smtplib
import time
from typing import TYPE_CHECKING

import yagmail

from domain.exceptions import MailError
from frameworks.logging_config import get_logger

if TYPE_CHECKING:
    from domain.thread_ref import ThreadRef

logger = get_logger("mail")

# 後方互換性のため再エクスポート
__all__ = ["MailError", "YagmailAdapter", "collapse_style_whitespace"]

# HTMLテンプレート名
EMAIL_TEMPLATE_NAME = "email_base.html.template"
EMAIL_FALLBACK_TEMPLATE = "email_fallback.html.template"

_STYLE_BLOCK_RE = re.compile(
    r"(<style[^>]*>)(.*?)(</style>)", re.DOTALL | re.IGNORECASE
)


def collapse_style_whitespace(html: str) -> str:
    """<style> ブロック内の空白・改行を単一スペースへ潰す。

    yagmail は本文の改行を `<br>` へ変換するため、`<style>` 内に改行が残ると
    CSS へ `<br>` が混入し、premailer のインライン化が全滅する（無スタイルで届く）。
    テンプレートの可読性は保ちたいので、送信直前にここで潰す。
    `<style>` の外側は触らない（本文の改行→`<br>` 変換は正常な挙動）。

    Args:
        html: 送信予定の HTML

    Returns:
        `<style>` 内のみ空白を畳んだ HTML
    """

    def _collapse(match: re.Match[str]) -> str:
        return (
            match.group(1)
            + re.sub(r"\s+", " ", match.group(2)).strip()
            + match.group(3)
        )

    return _STYLE_BLOCK_RE.sub(_collapse, html)


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
        # Stage 8: リトライポリシー設定化
        self._max_retries = config.mail_retry_count

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
                title_block = (
                    f'<h2 style="color: #f97316;">{title}</h2>' if title else ""
                )
                return render_template(
                    fallback_template, title_block=title_block, content=content
                )
            except Exception:
                # 最終手段: 最小限のHTML
                return f"<div>{content}</div>"

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        max_retries: int | None = None,
        *,
        message_id: str | None = None,
        thread: ThreadRef | None = None,
    ) -> None:
        """
        メールを送信する（指数バックオフ付きリトライ）。

        Args:
            to: 送信先（空の場合はデフォルト受信者）
            subject: 件名
            body: 本文（HTML可）
            max_retries: 最大リトライ回数（None時はConfig設定値を使用）
            message_id: 採番済み Message-ID（None時は yagmail が採番する）
            thread: 紐づけ先（None時はスレッドヘッダを載せない）

        Raises:
            MailError: 送信に失敗した場合

        Stage 8: リトライポリシー設定化
        デフォルトリトライ回数をConfigから読み込むよう変更
        """
        recipient = to if to else self._recipient
        # yagmail が改行を <br> に変換して CSS を壊すため、送信直前に <style> を畳む
        body = collapse_style_whitespace(body)
        # 空の辞書は渡さない——yagmail は headers が None でない場合だけ Date の
        # 自動付与を条件分岐するため、載せるものが無いときは None に倒す
        headers = thread.headers() if thread else None
        last_error: Exception | None = None
        # Stage 8: Configからのデフォルト値使用
        retries = max_retries if max_retries is not None else self._max_retries

        for attempt in range(retries):
            try:
                with yagmail.SMTP(self._sender, self._password) as yag:
                    yag.send(
                        to=recipient,
                        subject=subject,
                        contents=body,
                        message_id=message_id,
                        headers=headers or None,
                    )
                logger.info(f"Sent to: {recipient}")
                return
            except (
                smtplib.SMTPServerDisconnected,
                smtplib.SMTPConnectError,
                OSError,
            ) as e:
                # 一時的なネットワーク障害はリトライ
                last_error = e
                if attempt < retries - 1:
                    wait_time = 2**attempt  # 1s, 2s, 4s
                    logger.warning(
                        f"SMTP transient error, retry {attempt + 1}/{retries} in {wait_time}s: {e}"
                    )
                    time.sleep(wait_time)
            except smtplib.SMTPAuthenticationError as e:
                # 認証エラーはリトライしない
                raise MailError(f"Authentication failed: {e}") from e
            except Exception as e:
                # その他のエラーはリトライしない
                raise MailError(f"Failed to send email: {e}") from e

        # リトライ上限到達
        raise MailError(f"Failed after {retries} retries: {last_error}")

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

    def send_custom(
        self,
        subject: str,
        content: str,
        *,
        to: str = "",
        message_id: str | None = None,
        thread: ThreadRef | None = None,
    ) -> None:
        """
        カスタムコンテンツを送信する。

        content はプレーンテキストという約束なので、HTML へ埋める前に検疫する。
        これを欠いたまま送った 2026-08-26 の便では、本文に書いた HTML コメント
        記法が描画側に食われ、その語だけが抜けて届いた。エスケープは改行→段落
        タグの変換より**前**に行う（後だと足したタグ自身が実体参照になる）。
        quote=False なのは、content が要素の内容であって属性値ではないため
        （引用符を潰さない分、生 HTML を読むときに素直に読める）。

        Args:
            subject: 件名
            content: 本文（プレーンテキスト、改行はHTMLに変換）
            to: 送信先（空の場合はデフォルト受信者）
            message_id: 採番済み Message-ID（None時は yagmail が採番する）
            thread: 紐づけ先（None時はスレッドヘッダを載せない）
        """
        escaped = html.escape(content, quote=False)
        html_content = f"<p>{escaped.replace(chr(10), '</p><p>')}</p>"
        body = self._render_html(html_content)
        self.send(
            to=to or self._recipient,
            subject=subject,
            body=body,
            message_id=message_id,
            thread=thread,
        )
