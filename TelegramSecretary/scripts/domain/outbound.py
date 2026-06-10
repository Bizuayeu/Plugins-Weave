"""outbound 添付メディアの Domain 値オブジェクト。

Stage 8.1: エージェント起草の生成物（画像 / docx / PDF 等）を Telegram に送り返す際の
添付を Domain 表現する。bytes は持たず Path（identifier）のみ保持し、実バイト読み込みは
Adapter（送信時の open()）に閉じ込める（Stage 6 の MediaAttachment が identifier のみ
持つ方針と同型）。

送信前検証（存在 / サイズ）は FS I/O を伴うため UseCase 層
（usecases/outbound.py の validate_attachments）が担う——Domain は純ロジックのみを保つ。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# 画像として sendPhoto に振る拡張子。それ以外は sendDocument。
_PHOTO_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})


@dataclass(frozen=True)
class OutboundAttachment:
    """送信する添付ファイル。Path のみ保持（bytes は持たない、純粋性維持）。"""

    path: Path

    def is_photo(self) -> bool:
        """拡張子で sendPhoto / sendDocument を振り分ける（大文字小文字は正規化）。"""
        return self.path.suffix.lower() in _PHOTO_SUFFIXES
