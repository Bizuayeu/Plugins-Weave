from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

import pytest

from domain.exceptions import AttachmentTooLarge, LeaseConflictError
from domain.lease import SessionLease
from domain.models import OutboundMessage
from domain.outbound import OutboundAttachment
from usecases.proactive_send import ProactiveSend

from tests.usecases.fakes import FakeLeaseStore, FakeMessageSink


def _t(seconds: int = 0) -> datetime:
    base = datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=seconds)


def test_proactive_send_does_not_depend_on_offset_store():
    # 構造的保証: ProactiveSend は OffsetStore を依存に取らない＝offset を触れない
    # （offset は inbound 専用の既読台帳。advance すると未読 inbound を取りこぼす）
    init_params = inspect.signature(ProactiveSend.__init__).parameters
    assert "offset_store" not in init_params
    # execute も update_id を要求しない（inbound セマンティクスを持ち込まない）
    exec_params = inspect.signature(ProactiveSend.execute).parameters
    assert "update_id" not in exec_params


def test_successful_send_renews_lease():
    # 能動送信成功で sink に渡り、lease は renew（heartbeat 更新）。offset は構造的に不在
    sink = FakeMessageSink()
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = ProactiveSend(sink, lease_store)
    renewed = uc.execute(
        message=OutboundMessage(chat_id=100, text="関連する面白いトピックがありました"),
        lease=lease,
        now=_t(30),
    )

    assert len(sink.sent) == 1
    assert sink.sent[0].text == "関連する面白いトピックがありました"
    assert renewed.heartbeat == _t(30)
    assert lease_store.lease == renewed
    assert lease_store.save_calls == [renewed]


def test_send_failure_does_not_renew_lease():
    # 送信例外 → 伝播し lease 据え置き（renew されない）
    sink = FakeMessageSink(fail=True)
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = ProactiveSend(sink, lease_store)
    with pytest.raises(RuntimeError):
        uc.execute(
            message=OutboundMessage(chat_id=100, text="hi"),
            lease=lease,
            now=_t(30),
        )

    assert lease_store.lease == lease
    assert lease_store.save_calls == []


def test_send_raises_when_lease_was_stolen():
    # store に他人 lease（=奪取後）→ LeaseConflictError、送信せず他人 lease は触らない
    stolen = SessionLease(owner="other", heartbeat=_t(30), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=stolen)
    my_lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    sink = FakeMessageSink()

    uc = ProactiveSend(sink, lease_store)
    with pytest.raises(LeaseConflictError):
        uc.execute(
            message=OutboundMessage(chat_id=100, text="hi"),
            lease=my_lease,
            now=_t(40),
        )

    assert sink.sent == []
    assert lease_store.save_calls == []
    assert lease_store.lease == stolen


def test_send_raises_when_lease_was_released():
    # lease が release されて消えている → LeaseConflictError
    lease_store = FakeLeaseStore(initial=None)
    my_lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    sink = FakeMessageSink()

    uc = ProactiveSend(sink, lease_store)
    with pytest.raises(LeaseConflictError):
        uc.execute(
            message=OutboundMessage(chat_id=100, text="hi"),
            lease=my_lease,
            now=_t(40),
        )

    assert sink.sent == []
    assert lease_store.save_calls == []


def test_send_with_attachments_passes_them_to_sink(tmp_path):
    # 添付付き能動送信が attachments 込みで sink に渡り、成功で lease renew
    img = tmp_path / "fig.png"
    img.write_bytes(b"x" * 50)
    sink = FakeMessageSink()
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = ProactiveSend(sink, lease_store)
    msg = OutboundMessage(
        chat_id=100,
        text="figure",
        attachments=[OutboundAttachment(path=img)],
    )
    uc.execute(message=msg, lease=lease, now=_t(30), max_bytes=1024)

    assert len(sink.sent) == 1
    assert sink.sent[0].attachments[0].path == img
    assert lease_store.lease.heartbeat == _t(30)


def test_send_rejects_oversize_attachment_before_sending(tmp_path):
    # サイズ超過は送信前に弾く → sink 呼ばれず lease 据え置き（冪等・再送可能）
    big = tmp_path / "big.png"
    big.write_bytes(b"x" * 2048)
    sink = FakeMessageSink()
    lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=lease)

    uc = ProactiveSend(sink, lease_store)
    msg = OutboundMessage(
        chat_id=100,
        text="big",
        attachments=[OutboundAttachment(path=big)],
    )
    with pytest.raises(AttachmentTooLarge):
        uc.execute(message=msg, lease=lease, now=_t(30), max_bytes=1024)

    assert sink.sent == []
    assert lease_store.save_calls == []


def test_lease_check_precedes_attachment_validation(tmp_path):
    # lease 奪取済みなら、添付がサイズ超過でも LeaseConflictError が先（検証順序の保証）
    big = tmp_path / "big.png"
    big.write_bytes(b"x" * 2048)
    stolen = SessionLease(owner="other", heartbeat=_t(30), ttl_seconds=120)
    lease_store = FakeLeaseStore(initial=stolen)
    my_lease = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    sink = FakeMessageSink()

    uc = ProactiveSend(sink, lease_store)
    msg = OutboundMessage(
        chat_id=100,
        text="x",
        attachments=[OutboundAttachment(path=big)],
    )
    with pytest.raises(LeaseConflictError):
        uc.execute(message=msg, lease=my_lease, now=_t(40), max_bytes=1024)

    assert sink.sent == []
