"""markitdown ライブラリでドキュメント系 mime を md 化する Adapter（Stage 7.3）。

Adapter 内部で広く Exception を catch して RenderedMedia(render_status="failed") を返す
（Stage 6 の skip_reason と同型の「フラグ化、ブロックしない」スタンス）。
例外メッセージの絶対パス・file_id 全文は秘匿、stderr warning に file_id[:8] のみ短く出す。

mime-routing は UseCase 側（render_authorized_media._route_mime）が担い、
ここに来た時点で render 対象は確定している。
"""
from __future__ import annotations

from pathlib import Path

from adapters.media_failure import failed_render
from domain.media import MediaAttachment, RenderedMedia


class MarkitdownRenderer:
    """markitdown.MarkItDown を呼んで md 化する MediaRenderer Port 実装。

    MarkItDown instance は内部で magika という ML model を load して
    file type 推定をする（重い）ため、1 セッション 1 instance に留める。
    """

    def __init__(self) -> None:
        # 遅延 import: markitdown が未インストールの環境でも本モジュールの import
        # 自体は通る（adapter import を validate-config 等の軽量 path で踏ませない）
        from markitdown import MarkItDown

        self._md = MarkItDown()

    def render(self, media: MediaAttachment, local_path: Path) -> RenderedMedia:
        """local_path のファイルを md 化。失敗は flag 化、エージェント に正直に伝える。"""
        try:
            result = self._md.convert(str(local_path))
            rendered_text = result.text_content
        except Exception:
            # 絶対パス・file_id 全文は秘匿、stderr に短い warning のみ
            return failed_render(
                "markitdown-renderer", "render", "file_id", media.file_id[:8]
            )

        return RenderedMedia(rendered_text=rendered_text, render_status="ok")
