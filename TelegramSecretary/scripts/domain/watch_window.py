"""watch ループの wall-clock 窓。max_duration_seconds 経過で満了判定。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class WatchWindow:
    """watch が回り続ける時間窓。started_at + max_duration_seconds を超えたら満了。

    max_duration_seconds <= 0 は無限窓（既存 --max-iterations 0=無限 と同型セマンティクス）。
    """

    started_at: datetime
    max_duration_seconds: int

    def is_expired(self, now: datetime) -> bool:
        """now が started_at + max_duration を超えていれば満了。

        境界比較は SessionLease.is_stale と同一作法（ちょうどは False、超えたら True）。
        """
        if self.max_duration_seconds <= 0:
            return False
        return now > self.started_at + timedelta(seconds=self.max_duration_seconds)

    def remaining_seconds(self, now: datetime) -> float:
        """満了までの残り秒。満了後は負値、無限窓は inf（ログ/可観測性用途）。"""
        if self.max_duration_seconds <= 0:
            return float("inf")
        deadline = self.started_at + timedelta(seconds=self.max_duration_seconds)
        return (deadline - now).total_seconds()
