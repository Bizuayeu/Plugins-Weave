"""getUpdates → 認可フィルタ → 正規化 → injection フラグ → emit する UseCase。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from domain.authorization import AuthorizedChats
from domain.media import merge_caption_into_text
from domain.models import TelegramUpdate
from domain.normalize import flag_injection, normalize_input
from usecases.ports import OffsetStore, UpdateSource


@dataclass(frozen=True)
class NormalizedUpdate:
    """認可・正規化・フラグ判定済みの update。エージェント に渡す単位。"""

    update: TelegramUpdate
    normalized_text: str
    injection_flags: List[str]


class FetchAuthorizedUpdates:
    def __init__(
        self,
        source: UpdateSource,
        offset_store: OffsetStore,
        allowlist: AuthorizedChats,
    ) -> None:
        self._source = source
        self._offset_store = offset_store
        self._allowlist = allowlist

    def execute(self, timeout_seconds: int = 30) -> List[NormalizedUpdate]:
        """1 サイクル分の update を取得・認可・正規化して返す。

        - 未認可 chat の update は Domain で破棄、エージェント に渡さない
        - offset は取得した update 群（認可不問）の最大値に応じて advance（古い update の再取得を防ぐ）
        - Stage 6.2: caption は normalized_text に統合（merge_caption_into_text）、media は update に保持
        """
        offset = self._offset_store.load()
        updates = self._source.fetch(offset, timeout_seconds)

        if not updates:
            return []

        normalized_list: List[NormalizedUpdate] = []
        max_update_id = offset.value - 1
        for u in updates:
            if u.update_id > max_update_id:
                max_update_id = u.update_id
            if not self._allowlist.is_authorized(u.chat_id):
                continue
            text = normalize_input(u.text)
            merged = merge_caption_into_text(text, u.caption)
            flags = flag_injection(merged)
            normalized_list.append(
                NormalizedUpdate(update=u, normalized_text=merged, injection_flags=flags)
            )

        # 認可不問で取得した更新を全て消費したことを記録（offset advance）
        new_offset = offset.advance(max_update_id)
        self._offset_store.save(new_offset)
        return normalized_list
