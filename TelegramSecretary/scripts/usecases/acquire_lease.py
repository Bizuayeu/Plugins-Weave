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

        - 既存 lease なし → 新規取得（try_create＝排他作成。並走で負けたら再判定）
        - 既存 lease が stale → 奪取（crash 自己治癒）
        - 既存 lease が自分のもの → 更新（再開時の冪等）
        - 既存 lease が他人かつ fresh → LeaseConflictError
        """
        existing = self._store.load()
        self._raise_if_held_by_other(existing, now=now, owner=owner)
        new_lease = SessionLease(owner=owner, heartbeat=now, ttl_seconds=ttl_seconds)
        if existing is None:
            # 新規取得は load→check→save の TOCTOU を避け、排他作成で勝者を 1 つに絞る
            if self._store.try_create(new_lease):
                return new_lease
            # create 負け＝並走プロセスが先に取った。改めて先着者で判定し直す
            current = self._store.load()
            self._raise_if_held_by_other(current, now=now, owner=owner)
            # 先着者が既に stale（即 crash）or 自分（同 owner 再入）→ 上書きで取得
        self._store.save(new_lease)
        return new_lease

    @staticmethod
    def _raise_if_held_by_other(lease, now: datetime, owner: str) -> None:
        if lease is not None and lease.held_by_other(now=now, me=owner):
            raise LeaseConflictError(
                f"lease held by {lease.owner!r} until {lease.heartbeat.isoformat()}"
            )
