"""認可済み update の media を size 制限内で download する UseCase（Stage 6.2）。

実 I/O は Port（MediaDownloader）の向こう側。size 超過は内部で
MediaSizeLimitExceeded を raise → 同 UseCase 内で catch して
MediaDownloadResult.skip_reason="media_size_exceeded" に変換する。
download の通信失敗（CDN 4xx・期限切れ file_id 等）も skip_reason="download_failed"
にフラグ化する——fetch が download 前に offset を確定するため、ここで raise すると
当該バッチの全メッセージが再取得不能になる（watch 即死＝メッセージ消失）。
（Stage 1 の flag_injection 同型の「フラグ化して emit、ブロックはしない」原則）
唯一の例外は AuthFailureError（401）: exit 3 系の決定打なので伝播させる。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from domain.exceptions import (
    AuthFailureError,
    MediaSizeLimitExceeded,
    TelegramSecretaryError,
)
from domain.media import MediaAttachment
from usecases.fetch_authorized_updates import NormalizedUpdate
from usecases.ports import MediaDownloader


@dataclass(frozen=True)
class MediaDownloadResult:
    """download UseCase の結果。skip_reason 非 None なら skipped、local_path は None。"""

    update_id: int
    media: MediaAttachment
    local_path: Optional[Path]
    skip_reason: Optional[str]


class DownloadAuthorizedMedia:
    def __init__(self, downloader: MediaDownloader) -> None:
        self._downloader = downloader

    def execute(
        self,
        normalized_updates: List[NormalizedUpdate],
        target_dir: Path,
        max_size_bytes: int,
    ) -> List[MediaDownloadResult]:
        """各認可済み update の media を順に download。size 超過・通信失敗は skip。

        - size > max_size_bytes: skip_reason="media_size_exceeded"、downloader 呼ばず
        - download 通信失敗: skip_reason="download_failed"（AuthFailureError のみ伝播）
        - download 成功: local_path に保存先、skip_reason=None
        - 1 media の skip は他 media の download を妨げない
        """
        results: List[MediaDownloadResult] = []
        for nu in normalized_updates:
            for media in nu.update.media:
                try:
                    if media.size > max_size_bytes:
                        raise MediaSizeLimitExceeded(
                            f"size {media.size} > limit {max_size_bytes}"
                        )
                    local_path = self._downloader.download(media.file_id, target_dir)
                    results.append(
                        MediaDownloadResult(
                            update_id=nu.update.update_id,
                            media=media,
                            local_path=local_path,
                            skip_reason=None,
                        )
                    )
                except MediaSizeLimitExceeded:
                    results.append(
                        MediaDownloadResult(
                            update_id=nu.update.update_id,
                            media=media,
                            local_path=None,
                            skip_reason="media_size_exceeded",
                        )
                    )
                except AuthFailureError:
                    raise  # 401 は token 不正の決定打（exit 3 系）、フラグ化しない
                except TelegramSecretaryError:
                    results.append(
                        MediaDownloadResult(
                            update_id=nu.update.update_id,
                            media=media,
                            local_path=None,
                            skip_reason="download_failed",
                        )
                    )
        return results
