from __future__ import annotations

import pytest

from domain.media import MediaAttachment, RenderedMedia, merge_caption_into_text


# === MediaAttachment.from_photo_api ===

def test_media_from_photo_api_picks_largest_resolution():
    # Telegram 仕様: photo 配列の末尾が最大解像度
    photo_array = [
        {"file_id": "small", "file_size": 1024, "width": 90, "height": 90},
        {"file_id": "medium", "file_size": 8192, "width": 320, "height": 320},
        {"file_id": "large", "file_size": 102400, "width": 1280, "height": 1280},
    ]
    media = MediaAttachment.from_photo_api(photo_array)
    assert media is not None
    assert media.kind == "photo"
    assert media.file_id == "large"
    assert media.size == 102400
    assert media.mime_type == "image/jpeg"


def test_media_from_photo_api_single_resolution():
    photo_array = [{"file_id": "only", "file_size": 4096}]
    media = MediaAttachment.from_photo_api(photo_array)
    assert media is not None
    assert media.file_id == "only"
    assert media.size == 4096
    assert media.mime_type == "image/jpeg"


def test_media_from_photo_api_empty_returns_none():
    assert MediaAttachment.from_photo_api([]) is None


def test_media_from_photo_api_missing_file_size_defaults_to_zero():
    photo_array = [{"file_id": "no_size"}]
    media = MediaAttachment.from_photo_api(photo_array)
    assert media is not None
    assert media.size == 0


# === MediaAttachment.from_document_api ===

def test_media_from_document_api_full():
    document = {
        "file_id": "BQACAgIAA",
        "mime_type": "application/pdf",
        "file_size": 524288,
        "file_name": "contract.pdf",
    }
    media = MediaAttachment.from_document_api(document)
    assert media.kind == "document"
    assert media.file_id == "BQACAgIAA"
    assert media.mime_type == "application/pdf"
    assert media.size == 524288


def test_media_from_document_api_missing_mime_type_falls_back():
    document = {"file_id": "BQACAgIAA", "file_size": 1024}
    media = MediaAttachment.from_document_api(document)
    assert media.mime_type == "application/octet-stream"


def test_media_from_document_api_missing_file_size_defaults_to_zero():
    document = {"file_id": "BQACAgIAA"}
    media = MediaAttachment.from_document_api(document)
    assert media.size == 0


# === merge_caption_into_text ===

def test_merge_caption_into_text_both_present():
    assert merge_caption_into_text("hello", "Look at this") == "Look at this\nhello"


def test_merge_caption_into_text_no_caption():
    assert merge_caption_into_text("hello", None) == "hello"


def test_merge_caption_into_text_no_text():
    assert merge_caption_into_text("", "caption only") == "caption only"


def test_merge_caption_into_text_both_empty():
    assert merge_caption_into_text("", None) == ""


def test_merge_caption_into_text_empty_caption_treated_as_none():
    # caption が空文字も「欠落」として扱う（falsy 統一）
    assert merge_caption_into_text("hello", "") == "hello"


# === Immutability ===

def test_media_attachment_is_immutable():
    media = MediaAttachment(kind="photo", file_id="x", mime_type="image/jpeg", size=100)
    with pytest.raises(AttributeError):
        media.size = 200  # type: ignore[misc]


# === Stage 7.1: MediaAttachment.file_name ===

def test_media_from_document_api_extracts_file_name():
    """document に file_name があれば取り込む（エージェント の判断材料）。"""
    document = {
        "file_id": "BQACAgIAA",
        "mime_type": "application/pdf",
        "file_size": 1024,
        "file_name": "specification.pdf",
    }
    media = MediaAttachment.from_document_api(document)
    assert media.file_name == "specification.pdf"


def test_media_from_document_api_missing_file_name_returns_none():
    """file_name 欠落時は None（Telegram からファイル名が来ない稀ケース）。"""
    document = {"file_id": "BQACAgIAA", "file_size": 1024}
    media = MediaAttachment.from_document_api(document)
    assert media.file_name is None


def test_media_from_photo_api_has_no_file_name():
    """photo には file_name 概念がないため常に None。"""
    photo_array = [{"file_id": "p", "file_size": 1024}]
    media = MediaAttachment.from_photo_api(photo_array)
    assert media is not None
    assert media.file_name is None


def test_media_attachment_default_file_name_is_none():
    """既存呼び出し（file_name 未指定）が後方互換で動く。"""
    media = MediaAttachment(
        kind="photo", file_id="x", mime_type="image/jpeg", size=100
    )
    assert media.file_name is None


# === Stage 7.1: RenderedMedia ===

def test_rendered_media_holds_text_and_status():
    rendered = RenderedMedia(rendered_text="# 仕様書\n概要", render_status="ok")
    assert rendered.rendered_text == "# 仕様書\n概要"
    assert rendered.render_status == "ok"


def test_rendered_media_passthrough_has_no_text():
    """image/pdf 等 エージェント が直接読む形式は rendered_text=None で passthrough。"""
    rendered = RenderedMedia(rendered_text=None, render_status="passthrough")
    assert rendered.rendered_text is None
    assert rendered.render_status == "passthrough"


def test_rendered_media_skipped_status():
    """未対応 mime（音声/動画等）は skipped。"""
    rendered = RenderedMedia(rendered_text=None, render_status="skipped")
    assert rendered.render_status == "skipped"


def test_rendered_media_failed_status():
    """render を試みたが失敗した場合は failed、エージェント に正直に伝える。"""
    rendered = RenderedMedia(rendered_text=None, render_status="failed")
    assert rendered.render_status == "failed"


def test_rendered_media_rejects_invalid_status():
    """render_status は 4 状態のみ。Domain で構造的に保証。"""
    with pytest.raises(ValueError):
        RenderedMedia(rendered_text=None, render_status="unknown_state")


def test_rendered_media_is_immutable():
    rendered = RenderedMedia(rendered_text="x", render_status="ok")
    with pytest.raises(AttributeError):
        rendered.render_status = "failed"  # type: ignore[misc]


# === Stage 9.1: voice / audio / video / video_note ===

def test_media_from_voice_api():
    """Telegram voice（ボイスメモ）は OGG/OPUS。file_name 概念なし。"""
    voice = {
        "file_id": "AwACAgIAxxx",
        "duration": 5,
        "mime_type": "audio/ogg",
        "file_size": 8192,
    }
    media = MediaAttachment.from_voice_api(voice)
    assert media.kind == "voice"
    assert media.file_id == "AwACAgIAxxx"
    assert media.mime_type == "audio/ogg"
    assert media.size == 8192
    assert media.file_name is None


def test_media_from_voice_api_missing_mime_falls_back_to_ogg():
    """voice の mime 欠落時は audio/ogg（Telegram voice は常に OGG/OPUS）。"""
    voice = {"file_id": "v", "duration": 3}
    media = MediaAttachment.from_voice_api(voice)
    assert media.mime_type == "audio/ogg"
    assert media.size == 0


def test_media_from_audio_api():
    """audio（音楽ファイル）は file_name / mime_type を持ち得る。"""
    audio = {
        "file_id": "BAACAgIAyyy",
        "duration": 180,
        "mime_type": "audio/mpeg",
        "file_size": 3145728,
        "file_name": "song.mp3",
    }
    media = MediaAttachment.from_audio_api(audio)
    assert media.kind == "audio"
    assert media.file_id == "BAACAgIAyyy"
    assert media.mime_type == "audio/mpeg"
    assert media.size == 3145728
    assert media.file_name == "song.mp3"


def test_media_from_audio_api_missing_mime_falls_back():
    """audio の mime 欠落時は audio/mpeg（mp3 が最頻、audio/* prefix で routing）。"""
    audio = {"file_id": "a", "duration": 10}
    media = MediaAttachment.from_audio_api(audio)
    assert media.mime_type == "audio/mpeg"
    assert media.file_name is None


def test_media_from_video_api():
    """video（mp4）は file_name / mime_type を持ち得る。"""
    video = {
        "file_id": "BAACAgIAzzz",
        "width": 1280,
        "height": 720,
        "duration": 30,
        "mime_type": "video/mp4",
        "file_size": 10485760,
        "file_name": "clip.mp4",
    }
    media = MediaAttachment.from_video_api(video)
    assert media.kind == "video"
    assert media.file_id == "BAACAgIAzzz"
    assert media.mime_type == "video/mp4"
    assert media.size == 10485760
    assert media.file_name == "clip.mp4"


def test_media_from_video_api_missing_mime_falls_back_to_mp4():
    """video の mime 欠落時は video/mp4（Telegram video は mp4）。"""
    video = {"file_id": "v", "duration": 5}
    media = MediaAttachment.from_video_api(video)
    assert media.mime_type == "video/mp4"


def test_media_from_video_note_api():
    """video_note（丸いビデオメッセージ）は mime_type / file_name フィールドが無く常に mp4。"""
    video_note = {
        "file_id": "DQACAgIAwww",
        "length": 240,
        "duration": 8,
        "file_size": 524288,
    }
    media = MediaAttachment.from_video_note_api(video_note)
    assert media.kind == "video_note"
    assert media.file_id == "DQACAgIAwww"
    assert media.mime_type == "video/mp4"
    assert media.size == 524288
    assert media.file_name is None


def test_media_voice_is_immutable():
    """新 kind も frozen。"""
    media = MediaAttachment.from_voice_api({"file_id": "v"})
    with pytest.raises(AttributeError):
        media.kind = "audio"  # type: ignore[misc]


# === Stage 11.1: RenderedMedia derived_image_paths + page_count ===


def test_rendered_media_defaults_derived_images_empty_and_page_count_none():
    """既存構築（2 field のみ）が後方互換: derived_image_paths=[] / page_count=None。"""
    rendered = RenderedMedia(rendered_text="body", render_status="ok")
    assert rendered.derived_image_paths == []
    assert rendered.page_count is None


def test_rendered_media_holds_derived_images_and_page_count():
    """画像 PDF: 派生ページ画像パスと総ページ数を保持する。"""
    rendered = RenderedMedia(
        rendered_text="",
        render_status="ok",
        derived_image_paths=["a.png", "b.png"],
        page_count=12,
    )
    assert rendered.rendered_text == ""
    assert rendered.render_status == "ok"
    assert rendered.derived_image_paths == ["a.png", "b.png"]
    assert rendered.page_count == 12


def test_rendered_media_positional_construction_unbroken():
    """位置引数の既存構築 RenderedMedia(None, "passthrough") を壊さない（field 順序）。"""
    rendered = RenderedMedia(None, "passthrough")
    assert rendered.rendered_text is None
    assert rendered.render_status == "passthrough"
    assert rendered.derived_image_paths == []
    assert rendered.page_count is None


def test_rendered_media_default_derived_images_are_independent():
    """default_factory=list ゆえインスタンス毎に独立（共有ミュータブル default のバグ回避）。"""
    a = RenderedMedia(rendered_text="x", render_status="ok")
    b = RenderedMedia(rendered_text="y", render_status="ok")
    assert a.derived_image_paths is not b.derived_image_paths


def test_rendered_media_new_fields_immutable():
    """新 field も frozen（再代入で AttributeError）。"""
    rendered = RenderedMedia(
        rendered_text="",
        render_status="ok",
        derived_image_paths=["a.png"],
        page_count=1,
    )
    with pytest.raises(AttributeError):
        rendered.page_count = 2  # type: ignore[misc]


def test_rendered_media_status_validation_unchanged_with_new_fields():
    """render_status の 4 状態検証は新 field 追加後も不変。"""
    with pytest.raises(ValueError):
        RenderedMedia(
            rendered_text=None,
            render_status="bogus",
            derived_image_paths=["x.png"],
            page_count=1,
        )
