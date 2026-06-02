from __future__ import annotations

import io
import json

from adapters.state.emitter import StdoutEventEmitter
from domain.models import TelegramUpdate
from usecases.fetch_authorized_updates import NormalizedUpdate


def _normalized(text: str = "hi", flags=None) -> NormalizedUpdate:
    return NormalizedUpdate(
        update=TelegramUpdate(
            update_id=1, chat_id=100, user_id=200, username="test_user", text=text
        ),
        normalized_text=text,
        injection_flags=list(flags or []),
    )


def test_emit_writes_one_jsonline_per_update():
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized("hello"))
    line = stream.getvalue().strip()
    assert "\n" not in stream.getvalue().rstrip("\n")
    payload = json.loads(line)
    assert payload["update_id"] == 1
    assert payload["chat_id"] == 100
    assert payload["user_id"] == 200
    assert payload["text"] == "hello"


def test_emit_preserves_japanese():
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized("こんにちは"))
    out = stream.getvalue()
    # ensure_ascii=False で日本語そのまま出力
    assert "こんにちは" in out
    payload = json.loads(out.strip())
    assert payload["text"] == "こんにちは"


def test_emit_serializes_injection_flags():
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized("ignore previous", flags=["role_override"]))
    payload = json.loads(stream.getvalue().strip())
    assert payload["injection_flags"] == ["role_override"]


def test_emit_serializes_empty_flags_as_list():
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized("hi"))
    payload = json.loads(stream.getvalue().strip())
    assert payload["injection_flags"] == []


def test_emit_multiple_updates_writes_multiple_lines():
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized("first"))
    emitter.emit(_normalized("second"))
    lines = stream.getvalue().rstrip("\n").split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["text"] == "first"
    assert json.loads(lines[1])["text"] == "second"


# === Stage 6.3: emit v2 (media + version) ===

from pathlib import Path

from domain.media import MediaAttachment
from usecases.download_authorized_media import MediaDownloadResult


def _normalized_with_media(
    media: list[MediaAttachment], text: str = ""
) -> NormalizedUpdate:
    return NormalizedUpdate(
        update=TelegramUpdate(
            update_id=1,
            chat_id=100,
            user_id=200,
            username="test_user",
            text=text,
            media=media,
        ),
        normalized_text=text,
        injection_flags=[],
    )


def test_emit_includes_version_v2():
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized("hi"))
    payload = json.loads(stream.getvalue().strip())
    assert payload["v"] == 2


def test_emit_includes_empty_media_list_for_text_only():
    """text-only update でも `media: []` を明示出力（欠落≠未対応の混乱を避ける）。"""
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized("hi"))
    payload = json.loads(stream.getvalue().strip())
    assert payload["media"] == []


def test_emit_serializes_photo_media_without_local_path():
    """download_results なし（Medium モード）: media は出るが local_path は null。"""
    media = MediaAttachment(
        kind="photo", file_id="ABC123", mime_type="image/jpeg", size=4096
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]))
    payload = json.loads(stream.getvalue().strip())
    assert len(payload["media"]) == 1
    assert payload["media"][0]["kind"] == "photo"
    assert payload["media"][0]["file_id"] == "ABC123"
    assert payload["media"][0]["mime_type"] == "image/jpeg"
    assert payload["media"][0]["size"] == 4096
    assert payload["media"][0]["local_path"] is None
    assert payload["media"][0]["skip_reason"] is None


def test_emit_serializes_media_with_local_path_when_downloaded():
    """download_results 渡し（Heavy モード）: local_path が乗る。"""
    media = MediaAttachment(
        kind="photo", file_id="ABC123", mime_type="image/jpeg", size=4096
    )
    result = MediaDownloadResult(
        update_id=1,
        media=media,
        local_path=Path("/tmp/media/ABC123.jpg"),
        skip_reason=None,
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]), download_results=[result])
    payload = json.loads(stream.getvalue().strip())
    # OS 依存の path separator を許容
    assert payload["media"][0]["local_path"] is not None
    assert "ABC123.jpg" in payload["media"][0]["local_path"]
    assert payload["media"][0]["skip_reason"] is None


def test_emit_includes_skip_reason_for_size_exceeded():
    media = MediaAttachment(
        kind="photo", file_id="BIG", mime_type="image/jpeg", size=30_000_000
    )
    result = MediaDownloadResult(
        update_id=1,
        media=media,
        local_path=None,
        skip_reason="media_size_exceeded",
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]), download_results=[result])
    payload = json.loads(stream.getvalue().strip())
    assert payload["media"][0]["local_path"] is None
    assert payload["media"][0]["skip_reason"] == "media_size_exceeded"


# === Stage 7.3: rendered_text / render_status / file_name 出力 ===

from domain.media import RenderedMedia
from usecases.render_authorized_media import RenderResult


def _docx_media_attachment(file_name: str = "spec.docx") -> MediaAttachment:
    return MediaAttachment(
        kind="document",
        file_id="DOC123",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        size=4096,
        file_name=file_name,
    )


def test_emit_includes_file_name_for_document():
    media = _docx_media_attachment("specification.docx")
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]))
    payload = json.loads(stream.getvalue().strip())
    assert payload["media"][0]["file_name"] == "specification.docx"


def test_emit_file_name_is_null_for_photo():
    """photo には file_name 概念なし、出力は null（欠落≠未対応 の混乱回避）。"""
    media = MediaAttachment(
        kind="photo", file_id="P", mime_type="image/jpeg", size=4096
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]))
    payload = json.loads(stream.getvalue().strip())
    assert payload["media"][0]["file_name"] is None


def test_emit_serializes_rendered_text_and_status_from_render_results():
    """Heavy + render: render_results を渡すと rendered_text / render_status が乗る。"""
    media = _docx_media_attachment()
    rr = RenderResult(
        update_id=1,
        media=media,
        local_path=Path("/tmp/media/DOC123_spec.docx"),
        skip_reason=None,
        rendered=RenderedMedia(rendered_text="# 仕様書\n概要", render_status="ok"),
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]), render_results=[rr])
    payload = json.loads(stream.getvalue().strip())
    assert payload["media"][0]["render_status"] == "ok"
    assert payload["media"][0]["rendered_text"] == "# 仕様書\n概要"
    assert payload["media"][0]["local_path"] is not None
    assert "spec.docx" in payload["media"][0]["local_path"]


def test_emit_passthrough_render_status_for_photo_with_render_results():
    """image/pdf 等 passthrough: rendered_text=null + render_status='passthrough'。"""
    media = MediaAttachment(
        kind="photo", file_id="P", mime_type="image/jpeg", size=4096
    )
    rr = RenderResult(
        update_id=1,
        media=media,
        local_path=Path("/tmp/media/P.jpg"),
        skip_reason=None,
        rendered=RenderedMedia(rendered_text=None, render_status="passthrough"),
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]), render_results=[rr])
    payload = json.loads(stream.getvalue().strip())
    assert payload["media"][0]["render_status"] == "passthrough"
    assert payload["media"][0]["rendered_text"] is None


def test_emit_failed_render_status_keeps_local_path():
    """render 失敗: local_path は残るが rendered_text=null + render_status='failed'。"""
    media = _docx_media_attachment("broken.docx")
    rr = RenderResult(
        update_id=1,
        media=media,
        local_path=Path("/tmp/media/DOC123_broken.docx"),
        skip_reason=None,
        rendered=RenderedMedia(rendered_text=None, render_status="failed"),
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]), render_results=[rr])
    payload = json.loads(stream.getvalue().strip())
    assert payload["media"][0]["render_status"] == "failed"
    assert payload["media"][0]["rendered_text"] is None
    assert payload["media"][0]["local_path"] is not None


def test_emit_without_render_results_outputs_null_render_fields():
    """後方互換: render_results 未指定なら rendered_text / render_status は null。"""
    media = _docx_media_attachment()
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]))
    payload = json.loads(stream.getvalue().strip())
    assert payload["media"][0]["rendered_text"] is None
    assert payload["media"][0]["render_status"] is None


# === message_id: reply threading の入力源を emit に乗せる ===


def test_emit_includes_message_id():
    """ROUTINE_PROMPT が --reply-to に使う message_id を emit に出力する。"""
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(
        NormalizedUpdate(
            update=TelegramUpdate(
                update_id=1,
                chat_id=100,
                user_id=200,
                username="test_user",
                text="hi",
                message_id=678,
            ),
            normalized_text="hi",
            injection_flags=[],
        )
    )
    payload = json.loads(stream.getvalue().strip())
    assert payload["message_id"] == 678


def test_emit_message_id_null_when_absent():
    """message_id 欠落時は null を明示出力（欠落≠未対応の混乱回避）。"""
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized("hi"))
    payload = json.loads(stream.getvalue().strip())
    assert payload["message_id"] is None


# === Stage 11.2: derived_image_paths / page_count 出力（v2 維持、フィールド追加のみ）===


def _pdf_media_attachment(file_name: str = "drawings.pdf") -> MediaAttachment:
    return MediaAttachment(
        kind="document",
        file_id="PDF123",
        mime_type="application/pdf",
        size=3145728,
        file_name=file_name,
    )


def test_emit_serializes_derived_image_paths_and_page_count_for_image_pdf():
    """画像 PDF: render_results の derived_image_paths / page_count が payload に乗る。"""
    media = _pdf_media_attachment()
    rr = RenderResult(
        update_id=1,
        media=media,
        local_path=Path("/tmp/media/PDF123_drawings.pdf"),
        skip_reason=None,
        rendered=RenderedMedia(
            rendered_text="",
            render_status="ok",
            derived_image_paths=[
                "/tmp/media/PDF123_page-001.png",
                "/tmp/media/PDF123_page-002.png",
            ],
            page_count=12,
        ),
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]), render_results=[rr])
    item = json.loads(stream.getvalue().strip())["media"][0]
    assert item["page_count"] == 12
    assert len(item["derived_image_paths"]) == 2
    assert "page-001.png" in item["derived_image_paths"][0]
    assert item["rendered_text"] == ""
    assert item["render_status"] == "ok"


def test_emit_text_pdf_has_empty_derived_images_but_page_count():
    """テキスト PDF: derived_image_paths=[] だが page_count は乗る（両方明示）。"""
    media = _pdf_media_attachment("contract.pdf")
    rr = RenderResult(
        update_id=1,
        media=media,
        local_path=Path("/tmp/media/PDF123_contract.pdf"),
        skip_reason=None,
        rendered=RenderedMedia(
            rendered_text="--- page 1 ---\n本文",
            render_status="ok",
            derived_image_paths=[],
            page_count=3,
        ),
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]), render_results=[rr])
    item = json.loads(stream.getvalue().strip())["media"][0]
    assert item["derived_image_paths"] == []
    assert item["page_count"] == 3


def test_emit_without_render_results_defaults_derived_images_and_page_count():
    """後方互換: render_results 未指定なら derived_image_paths=[] / page_count=null。"""
    media = _pdf_media_attachment()
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]))
    item = json.loads(stream.getvalue().strip())["media"][0]
    assert item["derived_image_paths"] == []
    assert item["page_count"] is None


def test_emit_download_only_defaults_derived_images_and_page_count():
    """download_results のみ（render なし）: derived_image_paths=[] / page_count=null。"""
    media = _pdf_media_attachment()
    result = MediaDownloadResult(
        update_id=1,
        media=media,
        local_path=Path("/tmp/media/PDF123_drawings.pdf"),
        skip_reason=None,
    )
    stream = io.StringIO()
    emitter = StdoutEventEmitter(stream=stream)
    emitter.emit(_normalized_with_media([media]), download_results=[result])
    item = json.loads(stream.getvalue().strip())["media"][0]
    assert item["derived_image_paths"] == []
    assert item["page_count"] is None
