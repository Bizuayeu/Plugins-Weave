"""リース取得 UseCase。並走セッションの重複防止。"""
from __future__ import annotations

from datetime import datetime

from domain.exceptions import LeaseConflictError
from domain.lease import SessionLease
from usecases.ports import LeaseStore


class AcquireLease:
    def __init__(self, store: LeaseStore) -> None:
        self._store = store

    def execute(self, owner: str, now: datetime, ttl_seconds: int) -> SessionLease:
        """リースを取得する。

        - 既存 lease なし → 新規取得
        - 既存 lease が stale → 奪取（crash 自己治癒）
        - 既存 lease が自分のもの → 更新（再開時の冪等）
        - 既存 lease が他人かつ fresh → LeaseConflictError
        """
        existing = self._store.load()
        if existing is not None and existing.held_by_other(now=now, me=owner):
            raise LeaseConflictError(
                f"lease held by {existing.owner!r} until {existing.heartbeat.isoformat()}"
            )
        new_lease = SessionLease(owner=owner, heartbeat=now, ttl_seconds=ttl_seconds)
        self._store.save(new_lease)
        return new_lease
