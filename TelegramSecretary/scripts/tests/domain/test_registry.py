from __future__ import annotations

import pytest

from domain.registry import Ability, Identity, Individual, Knowledge, Task


# === Individual / Identity ===

def test_individual_round_trip():
    d = {
        "uuid": "u1", "display_name": "山田太郎",
        "role": "associate", "status": "active",
        "telegram_chat_id": 100, "line_user_id": None,
        "identity": {
            "category": "client", "relationship_label": "営業部長",
            "honorific": "山田さん", "tone": "polite", "context_notes": "",
            "priority_bias": "normal", "taboo_topics": [], "shared_with": [],
        },
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    }
    ind = Individual.from_dict(d)
    assert ind.uuid == "u1"
    assert ind.identity.tone == "polite"
    assert ind.to_dict() == d


def test_individual_rejects_invalid_role():
    with pytest.raises(ValueError):
        Individual(uuid="u", display_name="x", role="boss", status="active",
                   telegram_chat_id=None, line_user_id=None,
                   identity=Identity(), created_at="t", updated_at="t")


def test_individual_rejects_invalid_status():
    with pytest.raises(ValueError):
        Individual(uuid="u", display_name="x", role="associate", status="unknown",
                   telegram_chat_id=None, line_user_id=None,
                   identity=Identity(), created_at="t", updated_at="t")


def test_identity_rejects_invalid_tone():
    with pytest.raises(ValueError):
        Identity(tone="shouting")


def test_identity_defaults_are_safe():
    i = Identity()
    assert i.taboo_topics == []
    assert i.shared_with == []
    assert i.tone == "polite"


def test_individual_is_immutable():
    ind = Individual(uuid="u", display_name="x", role="associate", status="active",
                     telegram_chat_id=None, line_user_id=None,
                     identity=Identity(), created_at="t", updated_at="t")
    with pytest.raises(AttributeError):
        ind.status = "blocked"  # type: ignore[misc]


# === Task ===

def test_task_round_trip():
    d = {
        "id": "t1", "title": "見積依頼", "status": "open", "priority": "high",
        "due_date": "2026-06-01", "requester": "principal",
        "related_individuals": ["u1"], "notes": "",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
        "closed_at": None,
    }
    t = Task.from_dict(d)
    assert t.id == "t1"
    assert t.status == "open"
    assert t.to_dict() == d


def test_task_rejects_invalid_status():
    with pytest.raises(ValueError):
        Task(id="t", title="x", status="paused", priority="normal", due_date=None,
             requester="principal", related_individuals=[], notes="",
             created_at="t", updated_at="t", closed_at=None)


def test_task_rejects_invalid_priority():
    with pytest.raises(ValueError):
        Task(id="t", title="x", status="open", priority="urgent", due_date=None,
             requester="principal", related_individuals=[], notes="",
             created_at="t", updated_at="t", closed_at=None)


# === Knowledge ===

def test_knowledge_round_trip():
    d = {
        "id": "k1", "topic": "決済フロー", "category": "projects",
        "content": "判断と理由", "related": [], "sources": ["t1", "log-ref-1"],
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    }
    k = Knowledge.from_dict(d)
    assert k.topic == "決済フロー"
    assert k.category == "projects"
    assert k.to_dict() == d


def test_knowledge_requires_topic():
    with pytest.raises(ValueError):
        Knowledge(id="k", topic="", category="general", content="x",
                  related=[], sources=[], created_at="t", updated_at="t")


# === Ability ===

def test_ability_round_trip():
    d = {
        "id": "fortune-telling", "name": "占術鑑定",
        "trigger": "占い・鑑定・姓名判断・易・タロット・人物リーディング",
        "skill_path": "base-repo/skills/fortune-telling",
        "guidance": "占い依頼を受けたら SKILL.md を読み、鑑定書を生成して返す",
        "related": ["knowledge-id-1"],
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    }
    a = Ability.from_dict(d)
    assert a.id == "fortune-telling"
    assert a.name == "占術鑑定"
    assert a.skill_path == "base-repo/skills/fortune-telling"
    assert a.to_dict() == d


def test_ability_requires_name():
    with pytest.raises(ValueError):
        Ability(id="a", name="", trigger="x", skill_path="p", guidance="g",
                related=[], created_at="t", updated_at="t")


def test_ability_defaults_are_safe():
    a = Ability.from_dict({"id": "a", "name": "占い", "created_at": "t", "updated_at": "t"})
    assert a.trigger == ""
    assert a.skill_path == ""
    assert a.guidance == ""
    assert a.related == []


def test_ability_is_immutable():
    a = Ability(id="a", name="x", trigger="", skill_path="", guidance="",
                related=[], created_at="t", updated_at="t")
    with pytest.raises(AttributeError):
        a.name = "y"  # type: ignore[misc]


# === コレクション操作（upsert / find_by / remove_by 純関数） ===

from domain.registry import find_by, remove_by, upsert


def test_upsert_adds_new_record():
    out = upsert([], {"id": "a", "v": 1}, "id")
    assert out == [{"id": "a", "v": 1}]


def test_upsert_replaces_existing_in_place():
    records = [{"id": "a", "v": 1}, {"id": "b", "v": 9}]
    out = upsert(records, {"id": "a", "v": 2}, "id")
    assert out == [{"id": "a", "v": 2}, {"id": "b", "v": 9}]  # 順序保持・同位置置換


def test_upsert_does_not_mutate_input():
    records = [{"id": "a", "v": 1}]
    upsert(records, {"id": "b", "v": 2}, "id")
    assert records == [{"id": "a", "v": 1}]


def test_find_by_returns_match():
    assert find_by([{"id": "a"}, {"id": "b"}], "id", "b") == {"id": "b"}


def test_find_by_returns_none_when_absent():
    assert find_by([{"id": "a"}], "id", "z") is None


def test_remove_by_deletes_matching_record():
    out = remove_by([{"id": "a"}, {"id": "b"}], "id", "a")
    assert out == [{"id": "b"}]


def test_remove_by_returns_same_records_when_absent():
    out = remove_by([{"id": "a"}], "id", "z")
    assert out == [{"id": "a"}]


def test_remove_by_does_not_mutate_input():
    records = [{"id": "a"}, {"id": "b"}]
    remove_by(records, "id", "a")
    assert records == [{"id": "a"}, {"id": "b"}]


def test_remove_by_preserves_order_of_remaining():
    records = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    assert remove_by(records, "id", "b") == [{"id": "a"}, {"id": "c"}]
