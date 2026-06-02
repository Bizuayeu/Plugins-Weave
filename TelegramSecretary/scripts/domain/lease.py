"""並走セッション防止用の heartbeat + TTL リースロック。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    """timezone aware な UTC 現在時刻を返す。テストから差し替え可能な薄い関数。"""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class SessionLease:
    """Cloud Routine セッションが保持するリース。heartbeat + ttl_seconds で生存判定。"""

    owner: str
    heartbeat: datetime
    ttl_seconds: int

    def is_stale(self, now: datetime) -> bool:
        """now が heartbeat + TTL を超えていれば stale（奪取可能）。"""
        return now > self.heartbeat + timedelta(seconds=self.ttl_seconds)

    def held_by_other(self, now: datetime, me: str) -> bool:
        """他 owner が保持中かつ非 stale ならば True（取得失敗ライン）。"""
        return self.owner != me and not self.is_stale(now)

    def renew(self, now: datetime) -> "SessionLease":
        """heartbeat を now に更新した新しいリースを返す（frozen ゆえコピー）。"""
        return SessionLease(owner=self.owner, heartbeat=now, ttl_seconds=self.ttl_seconds)
