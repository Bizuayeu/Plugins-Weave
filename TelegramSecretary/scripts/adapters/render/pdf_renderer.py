"""pypdfium2 で PDF を画像化する MediaRenderer Port 実装（Stage 10 → 11 → 11.5）。

設計判断（Stage 11.5）: PDF は **常に画像化**する（テキスト層の有無を判定しない）。
スタンプ・薄いテキスト層の誤判定（全ページ同一の文書番号印で text 経路に落ちて中身が
読めない等）を構造的に排除する。エージェントは画像を Vision で大枠把握（ROUTINE_PROMPT: 最大5枚）
→ 必要なら以下をオンデマンド呼び出し:
  - extract_text(): 全ページのテキスト層を pdfplumber 抽出（--- page N --- マーカー）
  - rasterize_pages(start, end): 任意ページ範囲を画像化（cap=image_max_pages を超える
    21 枚目以降を個別要求された時用）

render() は先頭 image_max_pages 枚を画像化し rendered_text=""・page_count・derived_image_paths。
派生 png は local_path.parent（=state_dir/media/）フラット直下に local_path.stem プレフィックスで
保存する（media_downloader が {file_id}{ext} 命名するため stem==file_id、render と
rasterize_pages で命名が一貫）。既存 cleanup_media_dir の retention にそのまま乗る
（サブディレクトリを切ると retention から漏れ機密スキャン画像が残存する）。

例外は内部 catch → render_status="failed"（markitdown_renderer / moonshine_transcriber 同型、
クラッシュしない）。例外メッセージの絶対パス・file_id 全文は秘匿し、stderr に短い識別子のみ。
pdfplumber / pypdfium2 は遅延 import（cloud routine 起動を軽く保つ）。
mime-routing は UseCase 側（render_authorized_media._route_mime）が担う。
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from adapters.media_failure import failed_render, log_media_failure
from domain.media import MediaAttachment, RenderedMedia


class PdfRenderer:
    """PDF を常に画像化（MediaRenderer Port 実装）。テキストはオンデマンド extract_text。

    `RenderAuthorizedMedia` の pdf_renderer として注入。watch ループでは loop 外で
    1 インスタンス作り使い回す。pdfplumber / pypdfium2 import は lazy（初回呼び出し時）。
    """

    def __init__(self, image_max_pages: int = 20) -> None:
        # render() で画像化する先頭ページ数の cap（超多ページの disk/トークン暴走防止）。
        # 21 枚目以降は rasterize_pages でオンデマンド生成。エージェントの総量把握は page_count（総数）。
        self._image_max_pages = image_max_pages

    def render(self, media: MediaAttachment, local_path: Path) -> RenderedMedia:
        """PDF を先頭 image_max_pages 枚だけ画像化。判定はしない（常に画像経路）。"""
        try:
            import pypdfium2

            pdf = pypdfium2.PdfDocument(str(local_path))
            try:
                page_count = len(pdf)
                derived = self._rasterize_range(pdf, local_path, 0, self._image_max_pages)
            finally:
                pdf.close()
            return RenderedMedia(
                rendered_text="",
                render_status="ok",
                derived_image_paths=derived,
                page_count=page_count,
            )
        except Exception:
            return failed_render(
                "pdf-renderer", "render", "file_id", media.file_id[:8]
            )

    def extract_text(self, local_path: Path) -> RenderedMedia:
        """オンデマンド: 全ページのテキスト層を pdfplumber 抽出（--- page N --- マーカー）。

        エージェントが画像 Vision で大枠把握後「①全文テキスト」を選んだ時に呼ぶ（ROUTINE_PROMPT）。
        テキスト層が無い PDF（スキャン）は各ページ空 → rendered_text="" を返す（正直に）。
        """
        try:
            import pdfplumber

            page_texts: List[str] = []
            with pdfplumber.open(str(local_path)) as pdf:
                for page in pdf.pages:
                    page_texts.append(page.extract_text() or "")
            page_count = len(page_texts)
            if any(t.strip() for t in page_texts):
                marked = "\n".join(
                    f"--- page {i + 1} ---\n{t}" for i, t in enumerate(page_texts)
                )
                return RenderedMedia(
                    rendered_text=marked.strip(),
                    render_status="ok",
                    page_count=page_count,
                )
            return RenderedMedia(
                rendered_text="",
                render_status="ok",
                page_count=page_count,
            )
        except Exception:
            return failed_render(
                "pdf-renderer", "extract_text", "path", local_path.name[:8]
            )

    def rasterize_pages(self, local_path: Path, start: int, end: int) -> List[str]:
        """オンデマンド: [start, end)（0-indexed）ページを画像化しパス list を返す。

        render() の cap(image_max_pages) を超える 21 枚目以降を エージェントが「②個別ページ」で
        要求した時に呼ぶ。範囲は実ページ数でクランプ（はみ出しは黙ってクランプ、エラーにしない）。
        命名・保存先は render() と同一（local_path.stem プレフィックス＝一貫した file_id 由来）。
        """
        try:
            import pypdfium2

            pdf = pypdfium2.PdfDocument(str(local_path))
            try:
                return self._rasterize_range(pdf, local_path, start, end)
            finally:
                pdf.close()
        except Exception:
            log_media_failure(
                "pdf-renderer", "rasterize", "path", local_path.name[:8]
            )
            return []

    def _rasterize_range(
        self, pdf, local_path: Path, start: int, end: int
    ) -> List[str]:
        """開いた pdf の [start, end) ページを png 化（範囲は実ページ数でクランプ）。

        派生画像は local_path.parent フラット直下に local_path.stem プレフィックス命名で保存
        （media_downloader の {file_id}{ext} 命名により stem==file_id、cleanup_media_dir の
        is_file() フラット retention にそのまま乗る）。scale=2.0 は ~144dpi 相当で Vision 可読。
        ファイル名は 1-indexed の page 番号（doc_page-001.png）で エージェントのページ指定と一致。
        """
        target_dir = local_path.parent
        prefix = local_path.stem[:16]
        total = len(pdf)
        lo = max(0, start)
        hi = min(total, end)
        paths: List[str] = []
        for i in range(lo, hi):
            bitmap = pdf[i].render(scale=2.0)  # ~144dpi 相当、Vision 可読
            target = target_dir / f"{prefix}_page-{i + 1:03d}.png"
            bitmap.to_pil().save(str(target))
            paths.append(str(target))
        return paths
