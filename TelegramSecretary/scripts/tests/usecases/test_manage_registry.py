from __future__ import annotations

from tests.usecases.fakes import FakeRegistryStore as FakeStore
from usecases.manage_registry import RegistryService


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


def test_replace_all_drops_records_absent_from_the_new_set():
    """`add_or_update` の繰り返しでは表現できない「消えたレコード」を 1 回の save で反映する。"""
    store = FakeStore([{"id": "a"}, {"id": "b"}])
    svc = RegistryService(store, key_field="id")
    svc.replace_all([{"id": "b", "v": 2}])
    assert store.load() == [{"id": "b", "v": 2}]


def test_replace_all_does_not_alias_the_caller_list():
    """呼び出し側の配列を握らない——後から append された分が表に漏れ込む経路を塞ぐ。"""
    store = FakeStore()
    svc = RegistryService(store, key_field="id")
    records = [{"id": "a"}]
    svc.replace_all(records)
    records.append({"id": "b"})
    assert store.load() == [{"id": "a"}]
