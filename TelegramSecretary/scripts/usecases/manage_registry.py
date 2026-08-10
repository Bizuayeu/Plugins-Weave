"""管理表の汎用 CRUD UseCase。Store Port 越しに list / get / add_or_update / remove。"""

from __future__ import annotations

import builtins
from typing import Any

from domain.registry import find_by, remove_by, upsert
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

    @property
    def key_field(self) -> str:
        """この管理表のキー名（uuid / id）。WAL redo の registry_keys 収集に使う。"""
        return self._key

    def list(self) -> builtins.list[dict]:
        return self._store.load()

    def get(self, key_value: Any) -> dict | None:
        return find_by(self._store.load(), self._key, key_value)

    def add_or_update(self, record: dict) -> dict:
        records = upsert(self._store.load(), record, self._key)
        self._store.save(records)
        return record

    def remove(self, key_value: Any) -> None:
        self._store.save(remove_by(self._store.load(), self._key, key_value))

    def replace_all(self, records: builtins.list[dict]) -> None:
        """表の中身を丸ごと差し替える（import の正面口）。

        `add_or_update` の繰り返しでは「消えたレコード」を表現できない——全件を書き戻す
        操作をひとつの save に畳むことで、部分書き込みの中間状態が原理的に生じない
        （表は 1 ファイルゆえ何件でも 1 回の atomic write）。検証（値オブジェクト変換・
        語彙照合）は CRUD と同じく呼び出し側（CLI）の責務。
        """
        self._store.save(list(records))
