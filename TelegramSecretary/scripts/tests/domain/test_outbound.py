from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from domain.exceptions import AttachmentNotFound, AttachmentTooLarge
from domain.models import OutboundMessage
from domain.outbound import OutboundAttachment, validate_attachments


# === OutboundAttachment.is_photo ===

def test_is_photo_true_for_image_suffixes():
    for suffix in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        assert OutboundAttachment(path=Path(f"figure{suffix}")).is_photo() is True, suffix


def test_is_photo_false_for_document_suffixes():
    for suffix in (".docx", ".pdf", ".md", ".xlsx", ".txt"):
        assert OutboundAttachment(path=Path(f"report{suffix}")).is_photo() is False, suffix


def test_is_photo_normalizes_case():
    # Telegram 添付の拡張子は大文字でも来うる（OS 由来）。lower 正規化で判定。
    assert OutboundAttachment(path=Path("PHOTO.JPG")).is_photo() is True
    assert OutboundAttachment(path=Path("Photo.PnG")).is_photo() is True


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


# === OutboundMessage.attachments（後方互換） ===

def test_outbound_message_defaults_to_no_attachments():
    msg = OutboundMessage(chat_id=100, text="hi")
    assert msg.attachments == []


def test_outbound_message_carries_attachments():
    att = OutboundAttachment(path=Path("a.png"))
    msg = OutboundMessage(chat_id=100, text="caption", attachments=[att])
    assert msg.attachments == [att]
    assert msg.attachments[0].is_photo() is True


def test_outbound_message_is_frozen():
    msg = OutboundMessage(chat_id=1, text="x")
    with pytest.raises(FrozenInstanceError):
        msg.text = "y"  # type: ignore[misc]
