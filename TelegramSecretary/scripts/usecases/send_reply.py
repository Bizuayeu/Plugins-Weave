"""エージェント起草の返信を送信 → offset 永続化 → lease renew。"""
from __future__ import annotations

from datetime import datetime

from domain.lease import SessionLease
from domain.models import OutboundMessage
from usecases.outbound import validate_attachments, verify_owned_lease
from usecases.ports import LeaseStore, MessageSink, OffsetStore

# Telegram bot API の送信ファイル上限（公式 50MB）。CLI は env 値で上書きして渡す。
DEFAULT_OUTBOUND_MAX_BYTES = 50 * 1024 * 1024


class SendReply:
    def __init__(
        self,
        sink: MessageSink,
        offset_store: OffsetStore,
        lease_store: LeaseStore,
    ) -> None:
        self._sink = sink
        self._offset_store = offset_store
        self._lease_store = lease_store

    def execute(
        self,
        message: OutboundMessage,
        update_id: int,
        lease: SessionLease,
        now: datetime,
        max_bytes: int = DEFAULT_OUTBOUND_MAX_BYTES,
    ) -> SessionLease:
        """送信成功時のみ offset を advance、lease を renew する。

        - 送信前に現在の lease を再 load して、引数 `lease.owner` と一致するか検証。
          奪取されていれば LeaseConflictError（並走奪取への防御層）
        - lease 再検証の後・送信の前に添付を検証（存在/サイズ）。不正なら送信前に raise
          → sink は呼ばれず offset/lease 据え置き（冪等・再送可能）。添付なしは no-op
        - 送信失敗（例外伝播）時は offset/lease を変更しない。なお fetch 段で offset は
          advance 済みのため、ここでの advance は defense-in-depth——失敗分の再処理の実体は
          Telegram サーバ側の unconfirmed 再配送（新コンテナの fresh state_dir での再取得）が担う
        - 同じ update_id の advance は単調増加なので冪等
        """
        # 1. 並走防止：現在の lease 保持者が自分か確認（usecases.outbound 共有ヘルパ）
        current = verify_owned_lease(self._lease_store, lease.owner)

        # 2. 送信前検証：添付の存在/サイズを決定論的に弾く（lease 再検証の後・送信の前）
        validate_attachments(message.attachments, max_bytes)

        # 3. 送信を試行（失敗したら以降の永続化は走らない）
        self._sink.send(message)

        # 4. offset advance
        offset = self._offset_store.load()
        new_offset = offset.advance(update_id)
        self._offset_store.save(new_offset)

        # 5. lease renew（current を元に renew、引数 lease は古い snapshot の可能性）
        renewed = current.renew(now)
        self._lease_store.save(renewed)
        return renewed
