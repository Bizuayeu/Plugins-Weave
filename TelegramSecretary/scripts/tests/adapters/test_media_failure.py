"""adapters.media_failure の単体テスト（Stage 1: render 失敗定型の集約）。

render/transcribe Adapter が共有する「stderr に短縮 id を出す（絶対パス・全文 id は秘匿）→
RenderedMedia(failed) を返す」定型を 1 箇所に集約したヘルパの契約を pin する。
"""
from __future__ import annotations

from adapters.media_failure import failed_render, log_media_failure


def test_failed_render_returns_failed_and_logs_short_id(capsys):
    """failed_render は RenderedMedia(failed) を返し、stderr に短縮 id のみ出す。"""
    result = failed_render("pdf-renderer", "render", "file_id", "AgACAgIA")
    assert result.render_status == "failed"
    assert result.rendered_text is None

    err = capsys.readouterr().err
    assert "[pdf-renderer] failed to render file_id=AgACAgIA" in err


def test_log_media_failure_logs_only_returns_none(capsys):
    """log_media_failure はログのみ（戻り値 None）。rasterize_pages 等が [] を自前で返す用。"""
    ret = log_media_failure("pdf-renderer", "rasterize", "path", "doc12345")
    assert ret is None

    err = capsys.readouterr().err
    assert "[pdf-renderer] failed to rasterize path=doc12345" in err
