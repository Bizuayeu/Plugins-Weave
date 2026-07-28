"""認可 chat 単位の sliding window（超過分をエージェントへ渡さないための判定）。

allowlist は「誰が話しかけられるか」を絞るが「どれだけ話しかけられるか」は絞らない。
認可済み chat 由来のフラッド（誤ったループ・端末の暴走送信）はエージェント turn を
無制限に焚きうるため、窓で上限を掛ける。判定は純関数——履歴の保持は UseCase 側の責務。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

# 人手の連投では踏まず、暴走送信では踏む水準（1 分あたり 30 通）。
DEFAULT_WINDOW_SECONDS = 60
DEFAULT_MAX_EVENTS = 30


@dataclass(frozen=True)
class RateLimit:
    """直近 `window_seconds` 秒で `max_events` 件までを通す窓。

    `max_events <= 0` は無制限（`WatchWindow.max_duration_seconds <= 0` と同型セマンティクス）。
    """

    window_seconds: int = DEFAULT_WINDOW_SECONDS
    max_events: int = DEFAULT_MAX_EVENTS

    def admit(
        self, recent: Sequence[datetime], now: datetime
    ) -> tuple[bool, list[datetime]]:
        """`now` のイベントを通すかを判定し、更新後の履歴と共に返す。

        - 窓外に出た履歴は剪定する（境界作法は `WatchWindow.is_expired` と同一＝ちょうどは窓外）
        - 拒否したイベントは履歴に積まない——拒否された分が窓を占め続けると、
          フラッド中は永久に窓が開かなくなる
        """
        if self.max_events <= 0:
            return True, list(recent)
        horizon = timedelta(seconds=self.window_seconds)
        kept = [t for t in recent if now - t < horizon]
        if len(kept) >= self.max_events:
            return False, kept
        return True, [*kept, now]
