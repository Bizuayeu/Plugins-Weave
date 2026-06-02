"""outbound 添付メディアの Domain 値オブジェクトと送信前検証の純ロジック。

Stage 8.1: エージェント 起草の生成物（画像 / docx / PDF 等）を Telegram に送り返す際の
添付を Domain 表現する。bytes は持たず Path（identifier）のみ保持し、実バイト読み込みは
Adapter（送信時の open()）に閉じ込める（Stage 6 の MediaAttachment が identifier のみ
持つ方針と同型）。

送信前検証（存在 / サイズ）は「決定論的世界でコードが弾く」責務であり LLM 判断ではない。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from domain.exceptions import AttachmentNotFound, AttachmentTooLarge

# 画像として sendPhoto に振る拡張子。それ以外は sendDocument。
_PHOTO_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})


@dataclass(frozen=True)
class OutboundAttachment:
    """送信する添付ファイル。Path のみ保持（bytes は持たない、純粋性維持）。"""

    path: Path

    def is_photo(self) -> bool:
        """拡張子で sendPhoto / sendDocument を振り分ける（大文字小文字は正規化）。"""
        return self.path.suffix.lower() in _PHOTO_SUFFIXES


def validate_attachments(
    attachments: Sequence[OutboundAttachment], max_bytes: int
) -> None:
    """送信前に全添付の存在とサイズを検証する純ロジック。

    - パスがファイルとして存在しない → AttachmentNotFound
    - サイズが max_bytes を超える → AttachmentTooLarge
    空 list は no-op（text-only 送信の後方互換）。検証は全件に対して行う。
    """
    for attachment in attachments:
        path = attachment.path
        if not path.is_file():
            raise AttachmentNotFound(f"attachment not found: {path}")
        if path.stat().st_size > max_bytes:
            raise AttachmentTooLarge(f"attachment exceeds {max_bytes} bytes: {path}")
