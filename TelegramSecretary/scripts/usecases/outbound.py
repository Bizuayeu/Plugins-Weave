"""outbound 送信前ガード（lease 再検証・添付検証）の UseCase 層共有ヘルパ。

`SendReply` / `ProactiveSend` が完全に同型で持っていた「lease 再検証 → 添付検証 → 送信」
ブロックのうち、再利用可能な防御 2 枚をここに一本化する:

- verify_owned_lease: 現在の lease を再 load し owner 一致を検証（並走奪取への防御層）
- validate_attachments: 添付の存在/サイズ検証。domain/outbound.py から移動——
  FS I/O（is_file / stat）を実行するため「Domain は純ロジックのみ」規約から外れ、
  決定論的 I/O として UseCase 層に置く（値オブジェクト OutboundAttachment は domain に残る）

いずれも offset には一切触れない——`ProactiveSend` が OffsetStore を依存に持たない
構造保証（test_proactive_send.py が inspect で固定）を、ヘルパ共有後も無傷に保つ。
"""
from __future__ import annotations

from typing import Sequence

from domain.exceptions import (
    AttachmentNotFound,
    AttachmentTooLarge,
    LeaseConflictError,
)
from domain.lease import SessionLease
from domain.outbound import OutboundAttachment
from usecases.ports import LeaseStore


def verify_owned_lease(lease_store: LeaseStore, owner: str) -> SessionLease:
    """現在の lease を再 load し、owner 一致を検証して返す（送信直前の並走防止）。

    奪取・解放済みなら LeaseConflictError。戻り値は store 上の現在 lease で、
    呼び出し側はこれを renew の起点にする（呼び出し側が引数で受けた lease は
    古い snapshot の可能性があるため）。
    """
    current = lease_store.load()
    if current is None or current.owner != owner:
        current_owner = current.owner if current is not None else None
        raise LeaseConflictError(
            f"lease no longer held by {owner!r} (current owner: {current_owner!r})"
        )
    return current


def validate_attachments(
    attachments: Sequence[OutboundAttachment], max_bytes: int
) -> None:
    """送信前に全添付の存在とサイズを検証する（決定論的 I/O、LLM 判断ではない）。

    - パスがファイルとして存在しない → AttachmentNotFound
    - サイズが max_bytes を超える → AttachmentTooLarge
    空 list は no-op（text-only 送信の後方互換）。検証は全件に対して行う。
    """
    for attachment in attachments:
        path = attachment.path
        if not path.is_file():
            raise AttachmentNotFound(f"attachment not found: {path}")
        if path.stat().st_size > max_bytes:
            raise AttachmentTooLarge(f"attachment exceeds {max_bytes} bytes: {path}")
