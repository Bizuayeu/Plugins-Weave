from __future__ import annotations

import pytest

from domain.exceptions import AttachmentTooLarge, LeaseConflictError
from domain.lease import SessionLease
from domain.models import OutboundMessage
from domain.offset import UpdateOffset
from domain.outbound import OutboundAttachment
from usecases.send_reply import SendReply

from tests.usecases.fakes import FakeLeaseStore, FakeMessageSink, FakeOffsetStore


from tests.conftest import t_utc as _t


def test_successful_send_advances_offset_and_renews_lease():
    sink = FakeMessageSink()
    offset_store = FakeOffsetStore(initial=UpdateOffset(value=10))
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = SendReply(sink, offset_store, lease_store)
    renewed = uc.execute(
        message=OutboundMessage(chat_id=100, text="hi"),
        update_id=15,
        lease=lease,
        now=_t(30),
    )

    assert len(sink.sent) == 1
    assert sink.sent[0].text == "hi"
    assert offset_store.offset.value == 16  # max(10, 15+1)
    assert renewed.heartbeat == _t(30)
    assert lease_store.lease == renewed


def test_send_failure_does_not_advance_offset_or_renew_lease():
    sink = FakeMessageSink(fail=True)
    offset_store = FakeOffsetStore(initial=UpdateOffset(value=10))
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = SendReply(sink, offset_store, lease_store)
    with pytest.raises(RuntimeError):
        uc.execute(
            message=OutboundMessage(chat_id=100, text="hi"),
            update_id=15,
            lease=lease,
            now=_t(30),
        )

    # 送信失敗時は永続化が走らない（offset 据え置き / lease 据え置き）
    assert offset_store.offset.value == 10
    assert offset_store.save_calls == []
    assert lease_store.lease == lease
    assert lease_store.save_calls == []


def test_offset_advance_is_idempotent_with_smaller_update_id():
    # 既に進んでいる場合は巻き戻らない（再処理時の冪等性）
    sink = FakeMessageSink()
    offset_store = FakeOffsetStore(initial=UpdateOffset(value=20))
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = SendReply(sink, offset_store, lease_store)
    uc.execute(
        message=OutboundMessage(chat_id=100, text="hi"),
        update_id=5,
        lease=lease,
        now=_t(10),
    )
    assert offset_store.offset.value == 20  # max(20, 5+1) = 20


def test_send_raises_when_lease_was_stolen():
    # store には他人の lease（=奪取後の状態）
    stolen = SessionLease(owner="other", heartbeat=_t(30), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=stolen)

    # 我々が握っている古い lease snapshot
    my_lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)

    sink = FakeMessageSink()
    offset_store = FakeOffsetStore(initial=UpdateOffset(value=10))
    uc = SendReply(sink, offset_store, lease_store)
    with pytest.raises(LeaseConflictError):
        uc.execute(
            message=OutboundMessage(chat_id=100, text="hi"),
            update_id=15,
            lease=my_lease,
            now=_t(40),
        )
    # 何も書き換わらない（送信せず、offset 据え置き、他人 lease は触らない）
    assert sink.sent == []
    assert offset_store.save_calls == []
    assert lease_store.save_calls == []
    assert lease_store.lease == stolen


def test_send_raises_when_lease_was_released():
    # lease が release されて消えている状態
    lease_store = FakeLeaseStore(initial=None)
    my_lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)

    sink = FakeMessageSink()
    offset_store = FakeOffsetStore(initial=UpdateOffset(value=10))
    uc = SendReply(sink, offset_store, lease_store)
    with pytest.raises(LeaseConflictError):
        uc.execute(
            message=OutboundMessage(chat_id=100, text="hi"),
            update_id=15,
            lease=my_lease,
            now=_t(40),
        )
    assert sink.sent == []
    assert offset_store.save_calls == []


# === Stage 8.2: 添付対応 ===

def test_send_with_attachments_passes_them_to_sink(tmp_path):
    # 添付付き OutboundMessage が attachments 込みで sink に渡り、成功で offset/lease 進行
    img = tmp_path / "fig.png"
    img.write_bytes(b"x" * 50)
    sink = FakeMessageSink()
    offset_store = FakeOffsetStore(initial=UpdateOffset(value=10))
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = SendReply(sink, offset_store, lease_store)
    msg = OutboundMessage(
        chat_id=100,
        text="figure",
        attachments=[OutboundAttachment(path=img)],
    )
    uc.execute(message=msg, update_id=15, lease=lease, now=_t(30), max_bytes=1024)

    assert len(sink.sent) == 1
    assert sink.sent[0].attachments[0].path == img
    assert offset_store.offset.value == 16


def test_send_rejects_oversize_attachment_before_sending(tmp_path):
    # サイズ超過は送信前に弾く → sink 呼ばれず offset/lease 据え置き（冪等・再送可能）
    big = tmp_path / "big.png"
    big.write_bytes(b"x" * 2048)
    sink = FakeMessageSink()
    offset_store = FakeOffsetStore(initial=UpdateOffset(value=10))
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = SendReply(sink, offset_store, lease_store)
    msg = OutboundMessage(
        chat_id=100,
        text="big",
        attachments=[OutboundAttachment(path=big)],
    )
    with pytest.raises(AttachmentTooLarge):
        uc.execute(message=msg, update_id=15, lease=lease, now=_t(30), max_bytes=1024)

    assert sink.sent == []
    assert offset_store.save_calls == []
    assert lease_store.save_calls == []


def test_lease_check_precedes_attachment_validation(tmp_path):
    # lease 奪取済みなら、添付がサイズ超過でも LeaseConflictError が先（検証順序の保証）
    big = tmp_path / "big.png"
    big.write_bytes(b"x" * 2048)  # サイズ超過だが lease check が先に弾く
    stolen = SessionLease(owner="other", heartbeat=_t(30), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=stolen)
    my_lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    sink = FakeMessageSink()
    offset_store = FakeOffsetStore(initial=UpdateOffset(value=10))

    uc = SendReply(sink, offset_store, lease_store)
    msg = OutboundMessage(
        chat_id=100,
        text="x",
        attachments=[OutboundAttachment(path=big)],
    )
    with pytest.raises(LeaseConflictError):
        uc.execute(message=msg, update_id=15, lease=my_lease, now=_t(40), max_bytes=1024)

    assert sink.sent == []
