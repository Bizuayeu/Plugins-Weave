"""outbound 送信前ガード（lease 再検証・添付検証）の UseCase 層共有ヘルパ。

`SendReply` / `ProactiveSend` が完全に同型で持っていた「lease 再検証 → 添付検証 → 送信」
ブロックのうち、再利用可能な防御 2 枚をここに一本化する:

- verify_owned_lease: 現在の lease を再 load し owner 一致を検証（並走奪取への防御層）
- validate_attachments: 添付の存在/サイズ検証。domain/outbound.py から移動——
  FS I/O（is_file / stat）を実行するため「Domain は純ロジックのみ」規約から外れ、
  決定論的 I/O として UseCase 層に置く（値オブジェクト OutboundAttachment は domain に残る）
- scrub_outbound_text: 送信本文の漏洩スキャン（redact + 記録）。判定は Domain の
  redact_outbound、ここは適用点と観測ログの配線のみ

いずれも offset には一切触れない——`ProactiveSend` が OffsetStore を依存に持たない
構造保証（test_proactive_send.py が inspect で固定）を、ヘルパ共有後も無傷に保つ。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from domain.exceptions import (
    AttachmentNotFoundError,
    AttachmentTooLargeError,
    LeaseConflictError,
)
from domain.lease import SessionLease
from domain.models import OutboundMessage
from domain.outbound import OutboundAttachment
from domain.output_scan import redact_outbound
from usecases.observability import log_security_event
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

    - パスがファイルとして存在しない → AttachmentNotFoundError
    - サイズが max_bytes を超える → AttachmentTooLargeError
    空 list は no-op（text-only 送信の後方互換）。検証は全件に対して行う。
    """
    for attachment in attachments:
        path = attachment.path
        if not path.is_file():
            raise AttachmentNotFoundError(f"attachment not found: {path}")
        if path.stat().st_size > max_bytes:
            raise AttachmentTooLargeError(
                f"attachment exceeds {max_bytes} bytes: {path}"
            )


def scrub_outbound_text(message: OutboundMessage) -> OutboundMessage:
    """送信直前に本文をスキャンし、秘匿値の形状を伏せた message を返す。

    検出しても送信はブロックしない——混入部分だけ伏せ、何を伏せたかを stderr に残す
    （送信を止めると秘書が黙り、事故より障害の方が起きやすい）。検出名のみログし、
    伏せた実値は載せない。添付ファイルの中身は検査しない（SECURITY.md §4、エージェント責務）。
    """
    redacted, hits = redact_outbound(message.text)
    if not hits:
        return message
    log_security_event(
        "outbound_redacted", chat_id=message.chat_id, patterns=",".join(hits)
    )
    return replace(message, text=redacted)
