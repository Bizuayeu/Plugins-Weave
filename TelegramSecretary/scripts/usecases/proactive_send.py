"""エージェント起草の能動メッセージを送信 → lease renew（offset 非干渉）。

inbound（受信→返信）に紐づかない outbound（能動 push）を担う `SendReply` の姉妹 UseCase。
`SendReply` から OffsetStore 依存と offset advance を除いた同型——offset は inbound 専用の
既読台帳ゆえ、それを **依存に持たない** ことで「advance して未読 inbound を取りこぼす」事故を
構造的に封じる（提供する手段が無ければ壊しようがない）。lease 検証→添付検証→送信→renew の
順序と「送信失敗時は据え置き」不変条件は `SendReply` から継承する。
"""
from __future__ import annotations

from datetime import datetime

from domain.lease import SessionLease
from domain.models import OutboundMessage
from usecases.outbound import validate_attachments, verify_owned_lease
from usecases.ports import LeaseStore, MessageSink
from usecases.send_reply import DEFAULT_OUTBOUND_MAX_BYTES


class ProactiveSend:
    def __init__(
        self,
        sink: MessageSink,
        lease_store: LeaseStore,
    ) -> None:
        # OffsetStore を引数に取らない＝offset を構造的に触れない（inbound 専用台帳の保護）
        self._sink = sink
        self._lease_store = lease_store

    def execute(
        self,
        message: OutboundMessage,
        lease: SessionLease,
        now: datetime,
        max_bytes: int = DEFAULT_OUTBOUND_MAX_BYTES,
    ) -> SessionLease:
        """送信成功時のみ lease を renew する（offset には一切触れない）。

        - 送信前に現在の lease を再 load して、引数 `lease.owner` と一致するか検証。
          奪取されていれば LeaseConflictError（並走奪取への防御層）
        - lease 再検証の後・送信の前に添付を検証（存在/サイズ）。不正なら送信前に raise
          → sink は呼ばれず lease 据え置き。添付なしは no-op
        - 送信失敗（例外伝播）時は lease を変更しない
        """
        # 1. 並走防止：現在の lease 保持者が自分か確認（usecases.outbound 共有ヘルパ）
        current = verify_owned_lease(self._lease_store, lease.owner)

        # 2. 送信前検証：添付の存在/サイズを決定論的に弾く（lease 再検証の後・送信の前）
        validate_attachments(message.attachments, max_bytes)

        # 3. 送信を試行（失敗したら以降の永続化は走らない）
        self._sink.send(message)

        # 4. lease renew のみ（offset advance は無い＝inbound 専用の既読台帳に触れない）
        renewed = current.renew(now)
        self._lease_store.save(renewed)
        return renewed
