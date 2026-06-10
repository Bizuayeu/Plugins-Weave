"""usecases/outbound.py（送信前ガード共有ヘルパ）のテスト。

validate_attachments のテストは tests/domain/test_outbound.py から追従移動
（FS I/O を伴う検証は domain でなく usecases 層の責務）。verify_owned_lease は
SendReply / ProactiveSend から切り出した共有ヘルパの単体契約を固定する
（usecase 経由の結合挙動は test_send_reply.py / test_proactive_send.py が引き続き担保）。
"""
from __future__ import annotations

import pytest

from domain.exceptions import (
    AttachmentNotFound,
    AttachmentTooLarge,
    LeaseConflictError,
)
from domain.lease import SessionLease
from domain.outbound import OutboundAttachment
from usecases.outbound import validate_attachments, verify_owned_lease

from tests.conftest import t_utc as _t
from tests.usecases.fakes import FakeLeaseStore


# === verify_owned_lease ===

def test_verify_owned_lease_returns_current_lease():
    # owner 一致なら store 上の現在 lease を返す（renew の起点に使う）
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    store = FakeLeaseStore(initial=lease)
    assert verify_owned_lease(store, "me") == lease


def test_verify_owned_lease_raises_when_stolen():
    # store に他人 lease（=奪取後）→ LeaseConflictError
    store = FakeLeaseStore(initial=SessionLease(owner="other", heartbeat=_t(0), ttl_seconds=120))
    with pytest.raises(LeaseConflictError):
        verify_owned_lease(store, "me")


def test_verify_owned_lease_raises_when_released():
    # lease が release されて消えている → LeaseConflictError
    store = FakeLeaseStore(initial=None)
    with pytest.raises(LeaseConflictError):
        verify_owned_lease(store, "me")


# === validate_attachments ===

def test_validate_attachments_passes_for_valid_file(tmp_path):
    f = tmp_path / "ok.png"
    f.write_bytes(b"x" * 100)
    # 例外が出なければ合格（戻り値は無い）
    validate_attachments([OutboundAttachment(path=f)], max_bytes=1024)


def test_validate_attachments_raises_when_missing(tmp_path):
    with pytest.raises(AttachmentNotFound):
        validate_attachments(
            [OutboundAttachment(path=tmp_path / "nope.png")], max_bytes=1024
        )


def test_validate_attachments_raises_when_too_large(tmp_path):
    big = tmp_path / "big.bin"
    big.write_bytes(b"x" * 2048)
    with pytest.raises(AttachmentTooLarge):
        validate_attachments([OutboundAttachment(path=big)], max_bytes=1024)


def test_validate_attachments_empty_list_is_noop():
    # 添付なし（attachments=[]）は検証スルー＝従来 text-only 送信の後方互換
    validate_attachments([], max_bytes=1024)


def test_validate_attachments_checks_every_item(tmp_path):
    # 1件目は正常でも、2件目の不正で raise（全件検証）
    good = tmp_path / "good.png"
    good.write_bytes(b"x" * 10)
    with pytest.raises(AttachmentNotFound):
        validate_attachments(
            [
                OutboundAttachment(path=good),
                OutboundAttachment(path=tmp_path / "missing.pdf"),
            ],
            max_bytes=1024,
        )
