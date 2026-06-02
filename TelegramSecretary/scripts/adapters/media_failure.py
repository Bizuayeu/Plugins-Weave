"""メディア render/transcribe Adapter 共通の失敗ログ＋redact ヘルパ（Stage 1）。

render(markitdown / pdf)・transcribe(moonshine) Adapter が except 節で共通して行う
「stderr に短縮 id のみ出す（絶対パス・file_id 全文は秘匿）→ RenderedMedia(failed) を返す」
定型を 1 箇所に集約する。stderr I/O を含むため domain ではなく adapter 層に置く。
render/transcribe どちらの兄弟パッケージからも引けるよう adapters 直下に中立配置。

ident は呼び出し側で短縮済み（file_id[:8] / local_path.name[:8]）を渡す契約。
ここでは追加の切り詰めをしない（呼び出し側が「何を redact 済みとして渡すか」を決める）。
"""
from __future__ import annotations

import sys

from domain.media import RenderedMedia


def log_media_failure(tag: str, action: str, key: str, ident: str) -> None:
    """失敗を stderr に短く記録（絶対パス・全文 id は出さない）。

    戻り値が RenderedMedia でない呼び出し側（rasterize_pages の `[]` 等）はこれを直接使い、
    自前の空値を返す。
    """
    print(f"[{tag}] failed to {action} {key}={ident}", file=sys.stderr)


def failed_render(tag: str, action: str, key: str, ident: str) -> RenderedMedia:
    """log_media_failure した上で RenderedMedia(failed) を返す（render/extract_text/transcribe 用）。"""
    log_media_failure(tag, action, key, ident)
    return RenderedMedia(rendered_text=None, render_status="failed")
