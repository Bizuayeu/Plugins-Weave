"""getUpdates → 認可フィルタ → 正規化 → injection フラグ → emit する UseCase。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from domain.authorization import AuthorizedChats
from domain.lease import utc_now
from domain.media import merge_caption_into_text
from domain.models import TelegramUpdate
from domain.normalize import flag_injection, normalize_input
from domain.rate_limit import RateLimit
from usecases.observability import log_security_event
from usecases.ports import OffsetStore, UpdateSource


@dataclass(frozen=True)
class NormalizedUpdate:
    """認可・正規化・フラグ判定済みの update。エージェントに渡す単位。"""

    update: TelegramUpdate
    normalized_text: str
    injection_flags: list[str]


class FetchAuthorizedUpdates:
    def __init__(
        self,
        source: UpdateSource,
        offset_store: OffsetStore,
        allowlist: AuthorizedChats,
        rate_limit: RateLimit | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._source = source
        self._offset_store = offset_store
        self._allowlist = allowlist
        self._rate_limit = rate_limit if rate_limit is not None else RateLimit()
        self._clock = clock
        # chat_id ごとの直近 emit 時刻。watch プロセス内で保持する（プロセスを跨いで
        # 持ち越さない＝再起動で窓はリセットされる。永続化は必要が顕在化してから）
        self._recent: dict[int, list[datetime]] = {}

    def execute(self, timeout_seconds: int = 30) -> list[NormalizedUpdate]:
        """1 サイクル分の update を取得・認可・正規化して返す。

        - 未認可 chat の update は Domain で破棄、エージェントに渡さない（破棄は 1 行ログ）
        - 認可済みでも窓を超えた分は破棄する（レート制限。認可済みフラッドのコスト暴走を止める）
        - offset は取得した update 群（認可不問）の最大値に応じて advance（古い update の再取得を防ぐ）
        - caption は normalized_text に統合（merge_caption_into_text）、media は update に保持
        """
        offset = self._offset_store.load()
        updates = self._source.fetch(offset, timeout_seconds)

        if not updates:
            return []

        now = self._clock()
        normalized_list: list[NormalizedUpdate] = []
        max_update_id = offset.value - 1
        for u in updates:
            if u.update_id > max_update_id:
                max_update_id = u.update_id
            if not self._allowlist.is_authorized(u.chat_id):
                # 到達した未認可アクセスの観測点。本文は載せない（未信頼テキストをログに流さない）
                log_security_event(
                    "unauthorized_update_discarded",
                    chat_id=u.chat_id,
                    at=now.isoformat(),
                )
                continue
            admitted, history = self._rate_limit.admit(
                self._recent.get(u.chat_id, []), now
            )
            self._recent[u.chat_id] = history
            if not admitted:
                log_security_event(
                    "rate_limited_update_discarded",
                    chat_id=u.chat_id,
                    update_id=u.update_id,
                    at=now.isoformat(),
                )
                continue
            text = normalize_input(u.text)
            caption = normalize_input(u.caption) if u.caption else u.caption
            merged = merge_caption_into_text(text, caption)
            flags = flag_injection(merged)
            normalized_list.append(
                NormalizedUpdate(
                    update=u, normalized_text=merged, injection_flags=flags
                )
            )

        # 認可不問で取得した更新を全て消費したことを記録（offset advance）
        new_offset = offset.advance(max_update_id)
        self._offset_store.save(new_offset)
        return normalized_list
