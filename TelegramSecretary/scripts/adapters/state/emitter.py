"""Monitor が消費する JSON Lines 形式で `1 update = 1 行` を stdout 出力。"""
from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional, Sequence, TextIO

from usecases.download_authorized_media import MediaDownloadResult
from usecases.fetch_authorized_updates import NormalizedUpdate
from usecases.render_authorized_media import RenderResult

PAYLOAD_VERSION = 2


class StdoutEventEmitter:
    """`watch` モード時、認可・正規化済み update を JSON Lines で emit する。

    Stage 6.3: `v: 2` + `media[]` 拡張。download_results を渡せば local_path / skip_reason が乗る。
    Stage 7.3: `rendered_text` / `render_status` / `file_name` 追加（v2 維持、フィールド追加のみ）。
    render_results 優先（あれば local_path / skip_reason もそこから拾う）、なければ download_results、
    どちらもなければメタのみ。
    """

    def __init__(self, stream: Optional[TextIO] = None) -> None:
        self._stream = stream if stream is not None else sys.stdout

    def emit(
        self,
        update: NormalizedUpdate,
        download_results: Optional[Sequence[MediaDownloadResult]] = None,
        render_results: Optional[Sequence[RenderResult]] = None,
    ) -> None:
        media_payload = self._build_media_payload(
            update, download_results or [], render_results or []
        )
        payload: Dict[str, Any] = {
            "v": PAYLOAD_VERSION,
            "update_id": update.update.update_id,
            "message_id": update.update.message_id,
            "chat_id": update.update.chat_id,
            "user_id": update.update.user_id,
            "username": update.update.username,
            "text": update.normalized_text,
            "injection_flags": list(update.injection_flags),
            "media": media_payload,
        }
        self._stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._stream.flush()

    def _build_media_payload(
        self,
        update: NormalizedUpdate,
        download_results: Sequence[MediaDownloadResult],
        render_results: Sequence[RenderResult],
    ) -> List[Dict[str, Any]]:
        """update.update.media を JSON 化。
        render_results 優先（あれば local_path / skip_reason もそこから）、
        なければ download_results、どちらもなければメタのみ。"""
        download_by_file_id = {
            r.media.file_id: r
            for r in download_results
            if r.update_id == update.update.update_id
        }
        render_by_file_id = {
            r.media.file_id: r
            for r in render_results
            if r.update_id == update.update.update_id
        }
        out: List[Dict[str, Any]] = []
        for media in update.update.media:
            rd = render_by_file_id.get(media.file_id)
            dl = download_by_file_id.get(media.file_id)

            if rd is not None:
                local_path = str(rd.local_path) if rd.local_path is not None else None
                skip_reason = rd.skip_reason
                rendered_text = rd.rendered.rendered_text
                render_status = rd.rendered.render_status
                # Stage 11.2: 派生ページ画像と総ページ数は rd（render 済み）からのみ非空/非 null
                derived_image_paths = list(rd.rendered.derived_image_paths)
                page_count = rd.rendered.page_count
            elif dl is not None:
                local_path = str(dl.local_path) if dl.local_path is not None else None
                skip_reason = dl.skip_reason
                rendered_text = None
                render_status = None
                derived_image_paths = []
                page_count = None
            else:
                local_path = None
                skip_reason = None
                rendered_text = None
                render_status = None
                derived_image_paths = []
                page_count = None

            out.append(
                {
                    "kind": media.kind,
                    "file_id": media.file_id,
                    "file_name": media.file_name,
                    "mime_type": media.mime_type,
                    "size": media.size,
                    "local_path": local_path,
                    "skip_reason": skip_reason,
                    "rendered_text": rendered_text,
                    "render_status": render_status,
                    "page_count": page_count,
                    "derived_image_paths": derived_image_paths,
                }
            )
        return out
