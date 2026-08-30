# adapters/mail/ledger_recording_mail.py
"""
台帳記録メールデコレータ

MailPort を実装しつつ、内側の本物の MailPort へ委譲し、送信が成功したら
LedgerPort へ 1 行記録する。

送信経路の合流点（factories.get_mail_adapter）でこれを被せることで、
呼び出し側を一行も変えずに記録漏れをゼロにする。記録を規約（呼び出し側が
書き足す約束）で担保すると、今回のように書き写しが消えて記録が途切れる。

Stage 3: 送信経路の合流点を塞ぐ
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from domain.message_id import new_message_id

if TYPE_CHECKING:
    from domain.thread_ref import ThreadRef
    from usecases.ports import LedgerPort, MailPort

__all__ = ["LedgerRecordingMail"]


class LedgerRecordingMail:
    """
    送信を台帳へ記録する MailPort デコレータ。

    記録は送信が成功した後に行う（例外で終わった送信は台帳に載らない）。
    テストメール（test()）は委譲のみで記録しない。
    """

    def __init__(self, inner: MailPort, ledger: LedgerPort, recipient: str) -> None:
        """
        Args:
            inner: 実際に送信する MailPort
            ledger: 送信を記録する LedgerPort
            recipient: 既定の宛先（宛先未指定の送信を記録する際に使う）
        """
        self._inner = inner
        self._ledger = ledger
        self._recipient = recipient

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        *,
        message_id: str | None = None,
        thread: ThreadRef | None = None,
    ) -> None:
        """
        メールを送信し、台帳へ記録する。

        紐づけ先（thread）は送信ヘッダの話であって台帳の列ではないため、
        内側へ素通しするだけで記録には載せない。

        Args:
            to: 送信先（空の場合は既定の受信者）
            subject: 件名
            body: 本文
            message_id: 採番済み Message-ID（None時はここで採番する）
            thread: 紐づけ先（None時はスレッドヘッダを載せない）
        """
        mid = message_id or new_message_id()
        self._inner.send(to, subject, body, message_id=mid, thread=thread)
        self._record(mid, subject, to or self._recipient, body)

    def test(self) -> None:
        """テストメールを送信する（台帳には載せない）。"""
        self._inner.test()

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
        カスタムコンテンツを送信し、台帳へ記録する。

        台帳に残すのは HTML へ整形する前の content——読み返すのは人と LLM で、
        テンプレートのマークアップは索引の用を成さない（エスケープも同様に
        送信アダプタの領分であり、台帳には生の本文が残る）。

        Args:
            subject: 件名
            content: 本文（プレーンテキスト）
            to: 送信先（空の場合は既定の受信者）
            message_id: 採番済み Message-ID（None時はここで採番する）
            thread: 紐づけ先（None時はスレッドヘッダを載せない）
        """
        mid = message_id or new_message_id()
        self._inner.send_custom(subject, content, to=to, message_id=mid, thread=thread)
        self._record(mid, subject, to or self._recipient, content)

    def _record(self, message_id: str, subject: str, recipient: str, body: str) -> None:
        """
        台帳へ 1 行記録する。

        sent_at はここで採番する（アダプタ側は時刻を打たない設計）。
        """
        self._ledger.record_sent(
            message_id=message_id,
            sent_at=datetime.now().isoformat(),
            subject=subject,
            recipient=recipient,
            body=body,
        )
