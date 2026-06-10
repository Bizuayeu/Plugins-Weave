from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from domain.models import OutboundMessage
from domain.outbound import OutboundAttachment

# validate_attachments（FS I/O を伴う送信前検証）は usecases 層へ移動済み。
# テストも tests/usecases/test_outbound.py に追従移動（R-31）。


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
