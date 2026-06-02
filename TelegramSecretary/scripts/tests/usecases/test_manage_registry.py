from __future__ import annotations

from usecases.manage_registry import RegistryService


class FakeStore:
    """RegistryStore Port の fake（in-memory）。"""

    def __init__(self, initial=None):
        self._records = list(initial or [])

    def load(self):
        return list(self._records)

    def save(self, records):
        self._records = list(records)


def test_add_or_update_adds_new():
    store = FakeStore()
    svc = RegistryService(store, key_field="id")
    svc.add_or_update({"id": "a", "v": 1})
    assert store.load() == [{"id": "a", "v": 1}]


def test_add_or_update_replaces_existing():
    store = FakeStore([{"id": "a", "v": 1}])
    svc = RegistryService(store, key_field="id")
    svc.add_or_update({"id": "a", "v": 2})
    assert store.load() == [{"id": "a", "v": 2}]


def test_get_returns_record():
    svc = RegistryService(FakeStore([{"id": "a"}, {"id": "b"}]), key_field="id")
    assert svc.get("b") == {"id": "b"}


def test_get_returns_none_when_absent():
    svc = RegistryService(FakeStore(), key_field="id")
    assert svc.get("z") is None


def test_list_returns_all():
    svc = RegistryService(FakeStore([{"id": "a"}, {"id": "b"}]), key_field="id")
    assert svc.list() == [{"id": "a"}, {"id": "b"}]


def test_remove_deletes_by_key():
    store = FakeStore([{"id": "a"}, {"id": "b"}])
    svc = RegistryService(store, key_field="id")
    svc.remove("a")
    assert store.load() == [{"id": "b"}]
