"""メディア添付の Domain 値オブジェクトと caption 統合の純関数。

Stage 6.1: photo / document / caption を Domain 層の純粋型として表現する。
bytes は持たず file_id 等の identifier のみ保持（Infrastructure 層の local_path に閉じ込め）。
Stage 7.1: MediaAttachment.file_name 追加、RenderedMedia 値オブジェクト新設。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional, Sequence

# Stage 7.1: render_status の許容値（Domain で構造的に保証）
_VALID_RENDER_STATUSES = frozenset({"ok", "passthrough", "skipped", "failed"})


@dataclass(frozen=True)
class MediaAttachment:
    """Telegram message に含まれる各種メディアを Domain 表現したもの。"""

    kind: str  # "photo" | "document" | "voice" | "audio" | "video" | "video_note"
    file_id: str
    mime_type: str
    size: int
    file_name: Optional[str] = None  # Stage 7.1: document の元ファイル名（エージェント の判断材料）

    @classmethod
    def from_photo_api(
        cls, photo_array: Sequence[Mapping[str, Any]]
    ) -> Optional["MediaAttachment"]:
        """Telegram の photo 配列（複数解像度）から最大解像度を抽出。

        Telegram API 仕様で配列末尾が最大解像度。空配列なら None を返す。
        photo は常に jpeg（Telegram 側で正規化済み）。photo に file_name の概念は無い。
        """
        if not photo_array:
            return None
        largest = photo_array[-1]
        return cls(
            kind="photo",
            file_id=str(largest["file_id"]),
            mime_type="image/jpeg",
            size=int(largest.get("file_size", 0)),
        )

    @classmethod
    def from_document_api(cls, document: Mapping[str, Any]) -> "MediaAttachment":
        """Telegram の document から MediaAttachment を構築。

        mime_type 欠落時は application/octet-stream にフォールバック。
        Stage 7.1: file_name も抽出（欠落時 None）。
        """
        return cls(
            kind="document",
            file_id=str(document["file_id"]),
            mime_type=document.get("mime_type") or "application/octet-stream",
            size=int(document.get("file_size", 0)),
            file_name=document.get("file_name"),
        )

    @classmethod
    def from_voice_api(cls, voice: Mapping[str, Any]) -> "MediaAttachment":
        """Telegram の voice（ボイスメモ）から構築。

        voice は常に OGG/OPUS。mime 欠落時は audio/ogg にフォールバック。
        voice に file_name の概念は無い。
        """
        return cls(
            kind="voice",
            file_id=str(voice["file_id"]),
            mime_type=voice.get("mime_type") or "audio/ogg",
            size=int(voice.get("file_size", 0)),
        )

    @classmethod
    def from_audio_api(cls, audio: Mapping[str, Any]) -> "MediaAttachment":
        """Telegram の audio（音楽ファイル）から構築。

        mime 欠落時は audio/mpeg（mp3 が最頻、audio/* prefix で routing 可能）。
        audio は file_name を持ち得る。
        """
        return cls(
            kind="audio",
            file_id=str(audio["file_id"]),
            mime_type=audio.get("mime_type") or "audio/mpeg",
            size=int(audio.get("file_size", 0)),
            file_name=audio.get("file_name"),
        )

    @classmethod
    def from_video_api(cls, video: Mapping[str, Any]) -> "MediaAttachment":
        """Telegram の video（mp4）から構築。

        mime 欠落時は video/mp4。video は file_name を持ち得る。
        """
        return cls(
            kind="video",
            file_id=str(video["file_id"]),
            mime_type=video.get("mime_type") or "video/mp4",
            size=int(video.get("file_size", 0)),
            file_name=video.get("file_name"),
        )

    @classmethod
    def from_video_note_api(cls, video_note: Mapping[str, Any]) -> "MediaAttachment":
        """Telegram の video_note（丸いビデオメッセージ）から構築。

        video_note は mime_type / file_name フィールドを持たず常に mp4。
        """
        return cls(
            kind="video_note",
            file_id=str(video_note["file_id"]),
            mime_type="video/mp4",
            size=int(video_note.get("file_size", 0)),
        )


@dataclass(frozen=True)
class RenderedMedia:
    """MediaRenderer が返す render 結果（Stage 7.1）。

    render_status 四状態:
    - "ok": markitdown 等で md 化成功、rendered_text 非 None
    - "passthrough": image/pdf 等 エージェント が Read で直接読める形式、render 不要
    - "skipped": 未対応 mime（音声/動画等 Stage 7 射程外）、メタのみ
    - "failed": render を試みたが内部例外発生、エージェント に正直に伝える
    """

    rendered_text: Optional[str]
    render_status: str
    # Stage 11.1: 画像 PDF の派生ページ画像パス（動画 key frame と相乗りする共通基盤）。
    # str パスのみ保持し bytes は持たない（純粋性維持、MediaAttachment の identifier-only 方針と同型）。
    # 非画像 PDF・テキスト PDF・非 PDF は空 list（欠落≠未対応の明示、media:[] と同規律）。
    derived_image_paths: List[str] = field(default_factory=list)
    # Stage 11.1: PDF の総ページ数（両経路共通メタ）。エージェント が総量を把握して段階 Vision を判断する材料。
    # PDF 以外 / Stage 10 までの emit は None（後方互換）。
    page_count: Optional[int] = None

    def __post_init__(self) -> None:
        if self.render_status not in _VALID_RENDER_STATUSES:
            raise ValueError(
                f"render_status must be one of {sorted(_VALID_RENDER_STATUSES)}, "
                f"got {self.render_status!r}"
            )


def merge_caption_into_text(text: str, caption: Optional[str]) -> str:
    """画像/ドキュメントの caption を本文に統合する。

    両方あれば caption + "\\n" + text、片方欠落時は片方のみ、両方欠落時は空文字。
    空文字 caption は欠落として扱う（falsy 統一）。
    """
    if caption and text:
        return f"{caption}\n{text}"
    if caption:
        return caption
    return text or ""
