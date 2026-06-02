"""管理表の汎用 CRUD UseCase。Store Port 越しに list / get / add_or_update / remove。"""
from __future__ import annotations

from typing import Any, List, Optional

from domain.registry import find_by, upsert
from usecases.ports import RegistryStore


class RegistryService:
    """1 管理表に対する CRUD。`key_field` で各表のキー（uuid / id）を指定。

    records は dict ベース。値オブジェクト（Individual / Task / Knowledge）への
    変換・検証は呼び出し側（CLI）が担う。三世界分類: I/O は決定論的世界、
    「何を登録/更新するか」の判断は エージェント（重要度の世界）。
    """

    def __init__(self, store: RegistryStore, key_field: str) -> None:
        self._store = store
        self._key = key_field

    def list(self) -> List[dict]:
        return self._store.load()

    def get(self, key_value: Any) -> Optional[dict]:
        return find_by(self._store.load(), self._key, key_value)

    def add_or_update(self, record: dict) -> dict:
        records = upsert(self._store.load(), record, self._key)
        self._store.save(records)
        return record

    def remove(self, key_value: Any) -> None:
        records = [r for r in self._store.load() if r.get(self._key) != key_value]
        self._store.save(records)
