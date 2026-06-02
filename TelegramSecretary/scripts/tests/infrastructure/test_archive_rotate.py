from __future__ import annotations

from infrastructure.archive_rotate import partition_for_archive, split_by_category


# === partition_for_archive（TASKS/INDIVIDUALS 日付 Archive 用） ===

def test_partition_separates_by_predicate():
    records = [{"id": "a", "status": "done"}, {"id": "b", "status": "open"}]
    keep, archive = partition_for_archive(records, lambda r: r["status"] == "done")
    assert keep == [{"id": "b", "status": "open"}]
    assert archive == [{"id": "a", "status": "done"}]


def test_partition_preserves_order():
    records = [{"i": 1}, {"i": 2}, {"i": 3}, {"i": 4}]
    keep, archive = partition_for_archive(records, lambda r: r["i"] % 2 == 0)
    assert keep == [{"i": 1}, {"i": 3}]
    assert archive == [{"i": 2}, {"i": 4}]


def test_partition_empty():
    keep, archive = partition_for_archive([], lambda r: True)
    assert keep == []
    assert archive == []


# === split_by_category（KNOWLEDGE シャード分割用） ===

def test_split_by_category_groups():
    records = [
        {"id": "1", "category": "projects"},
        {"id": "2", "category": "clients"},
        {"id": "3", "category": "projects"},
    ]
    out = split_by_category(records)
    assert set(out.keys()) == {"projects", "clients"}
    assert len(out["projects"]) == 2
    assert len(out["clients"]) == 1


def test_split_by_category_defaults_uncategorized():
    out = split_by_category([{"id": "1"}])
    assert "general" in out
    assert out["general"] == [{"id": "1"}]


def test_split_by_category_preserves_order_within_group():
    records = [{"id": "1", "category": "x"}, {"id": "2", "category": "x"}]
    out = split_by_category(records)
    assert out["x"] == [{"id": "1", "category": "x"}, {"id": "2", "category": "x"}]
