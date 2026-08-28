# usecases/ingest_replies.py
"""
返信取り込みユースケース

台帳の Message-ID を鍵に、返ってきた返信だけを取り込む。
受信箱を横断検索はしない——自分が投げた球の跳ね返りだけを拾う（攻撃面の最小化）。

取り込んだ本文は外部入力であり、ReplyRecord.content_class がその素性を表明する
（ops-rules 7 のフェンシング）。判定はここで行い、受信箱の実装（IMAP か否か）
には依存しない。

Stage 4: IMAP による返信の取り込み
"""

from __future__ import annotations

from email.utils import parseaddr
from typing import TYPE_CHECKING

from frameworks.logging_config import get_logger

if TYPE_CHECKING:
    from domain.models import ReplyRecord

    from .ports import InboxPort, LedgerPort

logger = get_logger("replies")

__all__ = ["IngestRepliesUseCase", "normalize_message_id"]


def normalize_message_id(value: str) -> str:
    """
    Message-ID を突合可能な形へ正規化する。

    ヘッダの折り返し（CRLF + 空白）と角括弧の有無は経路によって揺れるため、
    空白を全て除いてから角括弧を外した形で比較する。

    Args:
        value: 生の Message-ID / In-Reply-To 値

    Returns:
        正規化された識別子
    """
    return "".join(value.split()).strip("<>")


class IngestRepliesUseCase:
    """返信取り込みユースケース"""

    def __init__(self, inbox: InboxPort, ledger: LedgerPort, recipient: str) -> None:
        """
        Args:
            inbox: InboxPort 実装
            ledger: LedgerPort 実装（台帳と返信の永続化）
            recipient: 送信先アドレス（返信の差出人として唯一許可する相手）
        """
        self._inbox = inbox
        self._ledger = ledger
        self._recipient = recipient

    def fetch(self) -> list[ReplyRecord]:
        """
        受信箱から返信を取り込む。

        取り込むのは「In-Reply-To が台帳の message_id と一致」かつ
        「From が送信先と一致」する返信のみ。冪等性は LedgerPort が
        返信自身の Message-ID で担保する。

        Returns:
            今回新たに追記された返信のリスト

        Raises:
            MailError: 受信箱への接続・認証・取得に失敗した場合
        """
        sent_ids = {
            normalize_message_id(r.message_id) for r in self._ledger.load_records()
        }

        ingested: list[ReplyRecord] = []
        for candidate in self._inbox.fetch_replies(self._recipient):
            if not self._is_accepted(candidate, sent_ids):
                continue
            if self._ledger.append_reply(candidate):
                ingested.append(candidate)

        logger.debug(f"Ingested replies: {len(ingested)}")
        return ingested

    def _is_accepted(self, candidate: ReplyRecord, sent_ids: set[str]) -> bool:
        """
        取り込み判定。

        Args:
            candidate: 受信箱から得た返信候補
            sent_ids: 台帳にある送信済み Message-ID（正規化済み）

        Returns:
            取り込む場合は True
        """
        if not normalize_message_id(candidate.message_id):
            # 冪等性の鍵が立たない候補は取り込まない
            logger.debug("Dropped a reply candidate without Message-ID")
            return False

        if normalize_message_id(candidate.in_reply_to) not in sent_ids:
            return False

        sender = parseaddr(candidate.sender)[1].casefold()
        return bool(sender) and sender == self._recipient.casefold()
