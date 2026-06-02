from __future__ import annotations

from pathlib import Path
from typing import Optional

from domain.media import MediaAttachment
from usecases.download_authorized_media import MediaDownloadResult
from usecases.render_authorized_media import RenderAuthorizedMedia

from tests.usecases.fakes import FakeMediaRenderer


def _download_result(
    update_id: int,
    mime_type: str,
    file_id: str = "x",
    skip_reason: Optional[str] = None,
    file_name: Optional[str] = None,
) -> MediaDownloadResult:
    """テスト用 helper: kind は mime から推定して MediaDownloadResult を組む。"""
    kind = "photo" if mime_type.startswith("image/") else "document"
    media = MediaAttachment(
        kind=kind,
        file_id=file_id,
        mime_type=mime_type,
        size=1024,
        file_name=file_name,
    )
    local_path = None if skip_reason else Path(f"/tmp/media/{file_id}.bin")
    return MediaDownloadResult(
        update_id=update_id,
        media=media,
        local_path=local_path,
        skip_reason=skip_reason,
    )


# === passthrough（Read tool が直接対応する形式）===

def test_image_jpeg_is_passthrough_without_renderer_call():
    dr = _download_result(1, "image/jpeg")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])

    assert len(results) == 1
    assert results[0].rendered.render_status == "passthrough"
    assert results[0].rendered.rendered_text is None
    assert renderer.render_calls == []


def test_image_png_is_passthrough():
    dr = _download_result(1, "image/png")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "passthrough"
    assert renderer.render_calls == []


def test_pdf_calls_pdf_renderer():
    """Stage 10: PDF は passthrough をやめ、pdf_renderer でテキスト層抽出（Read tool 非依存）。

    markitdown renderer（docx 等）には回さず、専用 pdf_renderer ルートに乗る。
    """
    dr = _download_result(1, "application/pdf", file_id="pdf")
    renderer = FakeMediaRenderer()
    pdf_renderer = FakeMediaRenderer(rendered_text="PDF 本文テキスト", render_status="ok")
    uc = RenderAuthorizedMedia(renderer, pdf_renderer=pdf_renderer)
    results = uc.execute([dr])

    assert results[0].rendered.render_status == "ok"
    assert results[0].rendered.rendered_text == "PDF 本文テキスト"
    assert len(pdf_renderer.render_calls) == 1  # pdf_renderer が呼ばれる
    assert renderer.render_calls == []  # markitdown renderer は呼ばれない


def test_pdf_skipped_without_pdf_renderer():
    """pdf_renderer 未注入なら PDF は skipped（後方互換・フォールバック、transcriber 同型）。"""
    dr = _download_result(1, "application/pdf")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)  # pdf_renderer なし
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"
    assert renderer.render_calls == []


def test_pdf_download_skip_propagates():
    """size 超過で download skip された PDF は render も skip（pdf_renderer 注入でも）。"""
    dr = _download_result(1, "application/pdf", skip_reason="media_size_exceeded")
    pdf_renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(FakeMediaRenderer(), pdf_renderer=pdf_renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"
    assert results[0].skip_reason == "media_size_exceeded"
    assert pdf_renderer.render_calls == []


def test_plain_text_is_passthrough():
    """text/plain は Read tool が直接対応するため markitdown を通す必要なし。"""
    dr = _download_result(1, "text/plain")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "passthrough"
    assert renderer.render_calls == []


def test_markdown_is_passthrough():
    dr = _download_result(1, "text/markdown")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "passthrough"


def test_json_is_passthrough():
    dr = _download_result(1, "application/json")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "passthrough"


# === render（markitdown で md 化）===

def test_docx_calls_renderer():
    dr = _download_result(
        1,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    renderer = FakeMediaRenderer(rendered_text="# docx 内容\n", render_status="ok")
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])

    assert results[0].rendered.render_status == "ok"
    assert results[0].rendered.rendered_text == "# docx 内容\n"
    assert len(renderer.render_calls) == 1


def test_pptx_calls_renderer():
    dr = _download_result(
        1,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    renderer = FakeMediaRenderer(rendered_text="# pptx スライド\n", render_status="ok")
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "ok"
    assert len(renderer.render_calls) == 1


def test_xlsx_calls_renderer():
    dr = _download_result(
        1,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    renderer = FakeMediaRenderer(rendered_text="| col |\n", render_status="ok")
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "ok"


def test_html_calls_renderer():
    """text/html は md 化に整形価値があるので render 経路。"""
    dr = _download_result(1, "text/html")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "ok"
    assert len(renderer.render_calls) == 1


# === skipped（未対応 mime / audio/video / 未知）===

def test_audio_is_skipped():
    dr = _download_result(1, "audio/mpeg")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"
    assert renderer.render_calls == []


def test_video_is_skipped():
    dr = _download_result(1, "video/mp4")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"


def test_unknown_mime_is_skipped():
    """未知 mime は保守的に skipped（エージェント に「読めない」を正直に渡す）。"""
    dr = _download_result(1, "application/octet-stream")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"
    assert renderer.render_calls == []


def test_zip_archive_is_skipped():
    dr = _download_result(1, "application/zip")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"


# === download skip 継承（size 超過等） ===

def test_skip_reason_propagates_to_render_skipped():
    """download 段階で skip された media（size 超過等）は render も skip。"""
    dr = _download_result(
        1,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        skip_reason="media_size_exceeded",
    )
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])

    assert results[0].rendered.render_status == "skipped"
    assert results[0].skip_reason == "media_size_exceeded"  # 継承
    assert results[0].local_path is None
    assert renderer.render_calls == []  # download 失敗時は render も呼ばない


# === 複数 + 空 ===

def test_processes_multiple_download_results_in_one_call():
    drs = [
        _download_result(1, "image/jpeg", file_id="img"),
        _download_result(
            2,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_id="docx",
        ),
        _download_result(3, "audio/mpeg", file_id="audio"),
    ]
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute(drs)

    assert len(results) == 3
    assert results[0].rendered.render_status == "passthrough"  # image
    assert results[1].rendered.render_status == "ok"  # docx
    assert results[2].rendered.render_status == "skipped"  # audio
    assert len(renderer.render_calls) == 1  # docx だけ


def test_empty_download_results_returns_empty():
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    assert uc.execute([]) == []


# === file_name / メタの引き継ぎ ===

def test_file_name_is_carried_through_render_result():
    """RenderResult が MediaAttachment の file_name を保持していること。"""
    dr = _download_result(
        1,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_id="docx",
        file_name="specification.docx",
    )
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)
    results = uc.execute([dr])
    assert results[0].media.file_name == "specification.docx"


# === Stage 9.4: audio → transcribe（transcriber 注入時のみ）===

def test_audio_mpeg_calls_transcriber_when_injected():
    """audio/mpeg は transcriber 注入時 transcribe ルート（markitdown renderer は呼ばない）。"""
    dr = _download_result(1, "audio/mpeg", file_id="aud")
    renderer = FakeMediaRenderer()
    transcriber = FakeMediaRenderer(rendered_text="文字起こしテキスト", render_status="ok")
    uc = RenderAuthorizedMedia(renderer, transcriber=transcriber)
    results = uc.execute([dr])

    assert results[0].rendered.render_status == "ok"
    assert results[0].rendered.rendered_text == "文字起こしテキスト"
    assert len(transcriber.render_calls) == 1  # transcriber が呼ばれる
    assert renderer.render_calls == []  # markitdown renderer は呼ばれない


def test_voice_ogg_calls_transcriber():
    """Telegram voice の audio/ogg も transcribe ルート。"""
    dr = _download_result(1, "audio/ogg", file_id="voice")
    transcriber = FakeMediaRenderer(rendered_text="ボイスメモ内容", render_status="ok")
    uc = RenderAuthorizedMedia(FakeMediaRenderer(), transcriber=transcriber)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "ok"
    assert len(transcriber.render_calls) == 1


def test_audio_skipped_without_transcriber():
    """transcriber 未注入なら audio は skipped（後方互換・フォールバック）。"""
    dr = _download_result(1, "audio/mpeg")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)  # transcriber なし
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"
    assert renderer.render_calls == []


def test_video_calls_transcriber():
    """Stage 9.6: video/* も transcribe ルート（音声トラックを transcript 化）。

    FfmpegAudioPreprocessor が動画コンテナの音声ストリームを PyAV で decode するため、
    audio/* と同じ transcriber 経路に乗る。key frame Vision は 9.6-ii で別途。
    """
    dr = _download_result(1, "video/mp4", file_id="vid")
    transcriber = FakeMediaRenderer(rendered_text="動画の音声トラック", render_status="ok")
    uc = RenderAuthorizedMedia(FakeMediaRenderer(), transcriber=transcriber)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "ok"
    assert results[0].rendered.rendered_text == "動画の音声トラック"
    assert len(transcriber.render_calls) == 1


def test_video_skipped_without_transcriber():
    """transcriber 未注入なら video も skipped（後方互換・フォールバック）。"""
    dr = _download_result(1, "video/mp4", file_id="vid")
    renderer = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(renderer)  # transcriber なし
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"
    assert renderer.render_calls == []


def test_audio_download_skip_propagates_even_with_transcriber():
    """size 超過で download skip された audio は transcribe も skip。"""
    dr = _download_result(1, "audio/mpeg", skip_reason="media_size_exceeded")
    transcriber = FakeMediaRenderer()
    uc = RenderAuthorizedMedia(FakeMediaRenderer(), transcriber=transcriber)
    results = uc.execute([dr])
    assert results[0].rendered.render_status == "skipped"
    assert results[0].skip_reason == "media_size_exceeded"
    assert transcriber.render_calls == []
