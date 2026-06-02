"""mime に応じた render 判定 + Port 経由 render 実行の UseCase（Stage 7.2）。

mime-routing は UseCase 側に閉じる:
- image/* → passthrough（Vision native）
- text/plain, text/csv, text/markdown, application/json → passthrough
- application/pdf → pdf（pdf_renderer 注入時のみ、Stage 10 でテキスト層抽出に移行。未注入なら skipped）
- docx, pptx, xlsx, text/html → render（markitdown 経由）
- audio/*, video/* → transcribe（transcriber 注入時のみ、Stage 9.4/9.6 音声 STT。動画は音声トラックを抽出。未注入なら skipped）
- archive 等その他 → skipped（key frame Vision は Stage 9.6-ii で別途）

download 段階で skip された media（size 超過等）は render も skip。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from domain.media import MediaAttachment, RenderedMedia
from usecases.download_authorized_media import MediaDownloadResult
from usecases.ports import MediaRenderer


_PASSTHROUGH_MIME_PREFIXES = ("image/",)
_PASSTHROUGH_MIME_EXACT = frozenset(
    {
        # Stage 10: application/pdf は passthrough から外し pdf ルート（テキスト層抽出）へ移行
        "text/plain",
        "text/csv",
        "text/markdown",
        "application/json",
    }
)
_PDF_MIME_EXACT = frozenset({"application/pdf"})  # Stage 10: pdfplumber でテキスト層抽出
_RENDER_MIME_EXACT = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "text/html",
    }
)
_TRANSCRIBE_MIME_PREFIXES = ("audio/", "video/")  # Stage 9.4/9.6: 音声・動画音声トラックを STT で transcript 化


@dataclass(frozen=True)
class RenderResult:
    """render UseCase の結果。MediaDownloadResult の延長として rendered を持つ。

    local_path / skip_reason は download_result からそのまま継承（emit 側で再利用）。
    """

    update_id: int
    media: MediaAttachment
    local_path: Optional[Path]
    skip_reason: Optional[str]
    rendered: RenderedMedia


def _route_mime(mime: str) -> str:
    """mime を `"passthrough" | "pdf" | "render" | "transcribe" | "skipped"` に分類する純関数。"""
    if any(mime.startswith(prefix) for prefix in _PASSTHROUGH_MIME_PREFIXES):
        return "passthrough"
    if mime in _PASSTHROUGH_MIME_EXACT:
        return "passthrough"
    if mime in _PDF_MIME_EXACT:
        return "pdf"
    if mime in _RENDER_MIME_EXACT:
        return "render"
    if any(mime.startswith(prefix) for prefix in _TRANSCRIBE_MIME_PREFIXES):
        return "transcribe"
    return "skipped"


class RenderAuthorizedMedia:
    def __init__(
        self,
        renderer: MediaRenderer,
        transcriber: Optional[MediaRenderer] = None,
        pdf_renderer: Optional[MediaRenderer] = None,
    ) -> None:
        self._renderer = renderer
        self._transcriber = transcriber
        self._pdf_renderer = pdf_renderer

    def execute(
        self,
        download_results: List[MediaDownloadResult],
    ) -> List[RenderResult]:
        """各 download_result を mime-routing し、必要なら renderer を呼ぶ。"""
        results: List[RenderResult] = []
        for dr in download_results:
            rendered = self._render_one(dr)
            results.append(
                RenderResult(
                    update_id=dr.update_id,
                    media=dr.media,
                    local_path=dr.local_path,
                    skip_reason=dr.skip_reason,
                    rendered=rendered,
                )
            )
        return results

    def _render_one(self, dr: MediaDownloadResult) -> RenderedMedia:
        # download skip された media（size 超過等）は render も skip
        if dr.skip_reason is not None or dr.local_path is None:
            return RenderedMedia(rendered_text=None, render_status="skipped")

        routing = _route_mime(dr.media.mime_type)
        if routing == "passthrough":
            return RenderedMedia(rendered_text=None, render_status="passthrough")
        if routing == "skipped":
            return RenderedMedia(rendered_text=None, render_status="skipped")
        if routing == "pdf":
            # PDF: pdf_renderer 注入時のみテキスト層抽出、未注入なら skipped にフォールバック
            # （Stage 10、transcriber 同型の後方互換）
            if self._pdf_renderer is None:
                return RenderedMedia(rendered_text=None, render_status="skipped")
            return self._pdf_renderer.render(dr.media, dr.local_path)
        if routing == "transcribe":
            # 音声: transcriber 注入時のみ transcribe、未注入なら skipped にフォールバック
            if self._transcriber is None:
                return RenderedMedia(rendered_text=None, render_status="skipped")
            return self._transcriber.render(dr.media, dr.local_path)
        # routing == "render"
        return self._renderer.render(dr.media, dr.local_path)
