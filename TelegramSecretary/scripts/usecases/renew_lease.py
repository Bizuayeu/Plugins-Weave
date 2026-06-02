"""リースの heartbeat 更新 UseCase。watch ループの定期 keep-alive に使う。"""
from __future__ import annotations

from datetime import datetime

from domain.exceptions import LeaseConflictError
from domain.lease import SessionLease
from usecases.ports import LeaseStore


class RenewLease:
    def __init__(self, store: LeaseStore) -> None:
        self._store = store

    def execute(self, owner: str, now: datetime) -> SessionLease:
        """自分が保持中のリースの heartbeat を更新する。

        - lease 不在 or 他人保持中なら LeaseConflictError（呼び出し側は exit 4）
        """
        existing = self._store.load()
        if existing is None:
            raise LeaseConflictError("no lease to renew")
        if existing.owner != owner:
            raise LeaseConflictError(f"lease owned by {existing.owner!r}, not {owner!r}")
        renewed = existing.renew(now)
        self._store.save(renewed)
        return renewed
