"""リース解放 UseCase。セッション終端で次 cron が拾えるようにする。"""
from __future__ import annotations

from usecases.ports import LeaseStore


class ReleaseLease:
    def __init__(self, store: LeaseStore) -> None:
        self._store = store

    def execute(self, owner: str) -> None:
        """自分のリースのみ解放する。他人のリースには触らない（誤解放防止）。"""
        existing = self._store.load()
        if existing is None:
            return
        if existing.owner != owner:
            return  # 他人のリースは触らない、silent no-op
        self._store.clear()
