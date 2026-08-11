"""mime に応じた render 判定 + Port 経由 render 実行の UseCase。

mime-routing は UseCase 側に閉じる:
- image/* → passthrough（Vision native）
- text/plain, text/csv, text/markdown, application/json → passthrough
- application/pdf → pdf（pdf_renderer 注入時のみテキスト層抽出。未注入なら skipped）
- docx, pptx, xlsx, text/html → render（markitdown 経由）
- audio/*, video/* → transcribe（transcriber 注入時のみ音声 STT。動画は音声トラックを抽出。未注入なら skipped）
- archive 等その他 → skipped（key frame Vision は別途）

download 段階で skip された media（size 超過等）は render も skip。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from domain.media import MediaAttachment, RenderedMedia
from domain.normalize import flag_injection, normalize_input
from usecases.download_authorized_media import MediaDownloadResult
from usecases.ports import MediaRenderer

_PASSTHROUGH_MIME_PREFIXES = ("image/",)
_PASSTHROUGH_MIME_EXACT = frozenset(
    {
        # application/pdf は passthrough から外し pdf ルート（テキスト層抽出）へ回す
        "text/plain",
        "text/csv",
        "text/markdown",
        "application/json",
    }
)
_PDF_MIME_EXACT = frozenset({"application/pdf"})  # pdfplumber でテキスト層抽出
_RENDER_MIME_EXACT = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
        "text/html",
    }
)
_TRANSCRIBE_MIME_PREFIXES = (
    "audio/",
    "video/",
)  # 音声・動画音声トラックを STT で transcript 化


@dataclass(frozen=True)
class RenderResult:
    """render UseCase の結果。MediaDownloadResult の延長として rendered を持つ。

    local_path / skip_reason は download_result からそのまま継承（emit 側で再利用）。
    """

    update_id: int
    media: MediaAttachment
    local_path: Path | None
    skip_reason: str | None
    rendered: RenderedMedia
    # 抽出本文（rendered_text / transcript）に対する injection フラグ。
    # 本文 text と同じく検知のみでブロックしない。emit 側で top-level へ合流する。
    injection_flags: list[str] = field(default_factory=list)


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


def _apply_input_defense(rendered: RenderedMedia) -> tuple[RenderedMedia, list[str]]:
    """抽出本文に本文 text と同じ入力防御を適用する純関数。

    添付（PDF/docx/pptx/xlsx）と音声 transcript は未信頼のバイナリ由来テキストであり、
    text/caption と同格の外部入力面。fetch 側と同じ順序（正規化 → フラグ判定）で扱い、
    異体字による回避を正規化が潰した上で検知する。ブロックはしない。
    """
    if not rendered.rendered_text:
        return rendered, []
    normalized = normalize_input(rendered.rendered_text)
    return replace(rendered, rendered_text=normalized), flag_injection(normalized)


class RenderAuthorizedMedia:
    def __init__(
        self,
        renderer: MediaRenderer,
        transcriber: MediaRenderer | None = None,
        pdf_renderer: MediaRenderer | None = None,
    ) -> None:
        self._renderer = renderer
        self._transcriber = transcriber
        self._pdf_renderer = pdf_renderer

    def execute(
        self,
        download_results: list[MediaDownloadResult],
    ) -> list[RenderResult]:
        """各 download_result を mime-routing し、必要なら renderer を呼ぶ。

        抽出できた本文には `_apply_input_defense` で正規化・フラグ判定を掛ける。
        """
        results: list[RenderResult] = []
        for dr in download_results:
            rendered, flags = _apply_input_defense(self._render_one(dr))
            results.append(
                RenderResult(
                    update_id=dr.update_id,
                    media=dr.media,
                    local_path=dr.local_path,
                    skip_reason=dr.skip_reason,
                    rendered=rendered,
                    injection_flags=flags,
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
            # （transcriber 同型の後方互換）
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
