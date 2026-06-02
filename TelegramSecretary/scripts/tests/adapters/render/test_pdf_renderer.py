from __future__ import annotations

from pathlib import Path

from domain.media import MediaAttachment
from adapters.render.pdf_renderer import PdfRenderer


def _make_pdf(path: Path, lines, font: str = "Helvetica") -> None:
    """テキスト層を持つ単一ページ PDF を reportlab で動的生成（fixture を git に置かない）。"""
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    c.setFont(font, 14)
    y = 800
    for ln in lines:
        c.drawString(50, y, ln)
        y -= 24
    c.showPage()
    c.save()


def _make_multipage_pdf(path: Path, pages, font: str = "Helvetica") -> None:
    """複数ページのテキスト層 PDF。pages[i] = i ページ目の行リスト。"""
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    for page_lines in pages:
        c.setFont(font, 14)
        y = 800
        for ln in page_lines:
            c.drawString(50, y, ln)
            y -= 24
        c.showPage()
    c.save()


def _make_multipage_blank_pdf(path: Path, n: int) -> None:
    """テキスト層ゼロの n ページ PDF（スキャン PDF 相当）。"""
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path))
    for _ in range(n):
        c.showPage()
    c.save()


def _pdf(file_id: str = "p") -> MediaAttachment:
    return MediaAttachment(
        kind="document",
        file_id=file_id,
        mime_type="application/pdf",
        size=100,
        file_name="doc.pdf",
    )


# === Stage 11.5: render は PDF を常に画像化（テキスト層判定を撤廃）===


def test_render_always_rasterizes_even_with_text_layer(tmp_path):
    """テキスト層があっても render は画像化する（判定しない＝Stage 11.5 の核心）。"""
    pdf = tmp_path / "text.pdf"
    _make_multipage_pdf(pdf, [["First page body"], ["Second page body"]])
    result = PdfRenderer().render(_pdf(), pdf)
    assert result.render_status == "ok"
    assert result.rendered_text == ""  # テキスト経路は廃止、常に画像
    assert result.page_count == 2
    assert len(result.derived_image_paths) == 2


def test_render_rasterizes_scan_pdf(tmp_path):
    """スキャン PDF（テキスト層ゼロ）も画像化（従来通り）。"""
    pdf = tmp_path / "scan.pdf"
    _make_multipage_blank_pdf(pdf, 3)
    result = PdfRenderer().render(_pdf(), pdf)
    assert result.render_status == "ok"
    assert result.rendered_text == ""
    assert result.page_count == 3
    assert len(result.derived_image_paths) == 3


def test_render_stamp_only_pdf_also_rasterizes(tmp_path):
    """全ページ同一スタンプの薄いテキスト層 PDF も画像化（誤判定が起きない）。

    旧実装では "WS25-00129" の薄い text 層で text 経路に落ち中身が読めなかった。
    判定撤廃により、スタンプ PDF も普通に画像化され Vision で読める。
    """
    pdf = tmp_path / "stamp.pdf"
    _make_multipage_pdf(pdf, [["WS25-00129"]] * 6)
    result = PdfRenderer().render(_pdf(), pdf)
    assert result.render_status == "ok"
    assert result.rendered_text == ""
    assert result.page_count == 6
    assert len(result.derived_image_paths) == 6


def test_render_derived_png_flat_with_stem_prefix(tmp_path):
    """派生 png は local_path.parent フラット直下、local_path.stem[:16] プレフィックス（=file_id）。"""
    pdf = tmp_path / "doc1234567890abcdef.pdf"
    _make_multipage_blank_pdf(pdf, 2)
    result = PdfRenderer().render(_pdf(), pdf)
    assert len(result.derived_image_paths) == 2
    for p in result.derived_image_paths:
        assert Path(p).exists()
        assert Path(p).suffix == ".png"
        assert Path(p).parent == tmp_path  # フラット直下（retention に乗る）
        assert Path(p).name.startswith("doc1234567890abc")  # stem[:16]


def test_render_respects_cap_but_page_count_is_total(tmp_path):
    """cap 超: derived は cap 枚で打ち切り、page_count は実総数（エージェント の総量把握用）。"""
    pdf = tmp_path / "many.pdf"
    _make_multipage_blank_pdf(pdf, 5)
    result = PdfRenderer(image_max_pages=2).render(_pdf(), pdf)
    assert result.render_status == "ok"
    assert len(result.derived_image_paths) == 2
    assert result.page_count == 5


def test_render_failed_on_broken_pdf(tmp_path):
    """壊れ PDF → failed、derived=[]、page_count=None（クラッシュなし）。"""
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"not a pdf \x00\x01")
    result = PdfRenderer().render(_pdf("abcdef1234"), broken)
    assert result.render_status == "failed"
    assert result.rendered_text is None
    assert result.derived_image_paths == []
    assert result.page_count is None


def test_render_failed_on_missing_file(tmp_path):
    """存在しないファイル → failed（内部 catch）。"""
    result = PdfRenderer().render(_pdf(), tmp_path / "nope.pdf")
    assert result.render_status == "failed"
    assert result.rendered_text is None


# === オンデマンド: extract_text（全文テキスト層抽出、--- page N --- マーカー）===


def test_extract_text_returns_page_markers(tmp_path):
    """テキスト PDF（複数ページ）→ --- page N --- マーカー入り本文 + page_count。"""
    pdf = tmp_path / "text.pdf"
    _make_multipage_pdf(pdf, [["First page body"], ["Second page body"]])
    result = PdfRenderer().extract_text(pdf)
    assert result.render_status == "ok"
    assert "--- page 1 ---" in result.rendered_text
    assert "--- page 2 ---" in result.rendered_text
    assert "First page body" in result.rendered_text
    assert "Second page body" in result.rendered_text
    assert result.page_count == 2


def test_extract_text_japanese(tmp_path):
    """日本語テキスト層 → 日本語抽出（CID フォント）。"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
    pdf = tmp_path / "jp.pdf"
    _make_pdf(pdf, ["日本語のテキスト層", "二行目の本文"], font="HeiseiKakuGo-W5")
    result = PdfRenderer().extract_text(pdf)
    assert result.render_status == "ok"
    assert "日本語のテキスト層" in result.rendered_text


def test_extract_text_empty_for_scan_pdf(tmp_path):
    """テキスト層ゼロのスキャン PDF → rendered_text=""（エージェント に正直に）。"""
    pdf = tmp_path / "scan.pdf"
    _make_multipage_blank_pdf(pdf, 2)
    result = PdfRenderer().extract_text(pdf)
    assert result.render_status == "ok"
    assert result.rendered_text == ""
    assert result.page_count == 2


def test_extract_text_failed_on_broken(tmp_path):
    """壊れ PDF → failed（クラッシュさせず正直に）。"""
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"not a pdf \x00\x01")
    result = PdfRenderer().extract_text(broken)
    assert result.render_status == "failed"
    assert result.rendered_text is None


# === オンデマンド: rasterize_pages（任意ページ範囲を画像化、cap 超の 21 枚目以降用）===


def test_rasterize_pages_returns_range(tmp_path):
    """[start, end)（0-indexed）の範囲を画像化、ファイル名は 1-indexed page 番号。"""
    pdf = tmp_path / "doc.pdf"
    _make_multipage_blank_pdf(pdf, 5)
    paths = PdfRenderer().rasterize_pages(pdf, 1, 3)  # page 2, 3
    assert len(paths) == 2
    for p in paths:
        assert Path(p).exists()
        assert Path(p).suffix == ".png"
    assert sorted(Path(p).name for p in paths) == ["doc_page-002.png", "doc_page-003.png"]


def test_rasterize_pages_clamps_to_total(tmp_path):
    """範囲が実ページ数を超えても総数でクランプ（はみ出しはエラーにしない）。"""
    pdf = tmp_path / "doc.pdf"
    _make_multipage_blank_pdf(pdf, 3)
    paths = PdfRenderer().rasterize_pages(pdf, 0, 99)
    assert len(paths) == 3


def test_rasterize_pages_beyond_cap(tmp_path):
    """cap=20 を超える 21 枚目以降を個別生成できる（オンデマンド ②の N>20）。"""
    pdf = tmp_path / "doc.pdf"
    _make_multipage_blank_pdf(pdf, 22)
    paths = PdfRenderer(image_max_pages=20).rasterize_pages(pdf, 20, 22)  # page 21, 22
    assert len(paths) == 2
    assert sorted(Path(p).name for p in paths) == ["doc_page-021.png", "doc_page-022.png"]


def test_rasterize_pages_failed_returns_empty(tmp_path):
    """壊れ PDF → 空 list（クラッシュなし）。"""
    broken = tmp_path / "broken.pdf"
    broken.write_bytes(b"not a pdf \x00\x01")
    paths = PdfRenderer().rasterize_pages(broken, 0, 5)
    assert paths == []
