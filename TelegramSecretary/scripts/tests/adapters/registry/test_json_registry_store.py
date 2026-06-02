from __future__ import annotations

from pathlib import Path

from adapters.registry.json_registry_store import JsonRegistryStore


def test_round_trip(tmp_path: Path):
    store = JsonRegistryStore(tmp_path / "individuals" / "INDIVIDUALS.json")
    records = [{"uuid": "u1", "name": "yamada"}, {"uuid": "u2"}]
    store.save(records)
    assert store.load() == records


def test_load_missing_file_returns_empty(tmp_path: Path):
    store = JsonRegistryStore(tmp_path / "nope.json")
    assert store.load() == []


def test_load_corrupt_file_returns_empty(tmp_path: Path):
    p = tmp_path / "broken.json"
    p.write_text("{ this is not json", encoding="utf-8")
    store = JsonRegistryStore(p)
    assert store.load() == []


def test_save_creates_parent_dirs(tmp_path: Path):
    store = JsonRegistryStore(tmp_path / "a" / "b" / "c.json")
    store.save([{"id": "x"}])
    assert store.load() == [{"id": "x"}]


def test_save_preserves_japanese(tmp_path: Path):
    store = JsonRegistryStore(tmp_path / "j.json")
    store.save([{"name": "山田太郎", "note": "営業部長"}])
    raw = (tmp_path / "j.json").read_text(encoding="utf-8")
    assert "山田太郎" in raw  # ensure_ascii=False
