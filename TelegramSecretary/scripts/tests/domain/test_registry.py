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


# === Profile（P軸データ） ===

from domain.registry import Goal, Profile, Step, derive_role


def test_profile_round_trip():
    d = {
        "id": "p1", "subject": "principal", "method": "mbti",
        "content": "INTJ。長期計画を好み、締切前倒しの段取りが響く",
        "traits": ["計画的", "内省的"], "sources": ["対話 2026-06-12"],
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    }
    p = Profile.from_dict(d)
    assert p.subject == "principal"
    assert p.method == "mbti"
    assert p.to_dict() == d


def test_profile_rejects_invalid_method():
    with pytest.raises(ValueError):
        Profile(id="p", subject="principal", method="palm_reading", content="",
                traits=[], sources=[], created_at="t", updated_at="t")


def test_profile_requires_subject():
    with pytest.raises(ValueError):
        Profile(id="p", subject="", method="mbti", content="",
                traits=[], sources=[], created_at="t", updated_at="t")


def test_profile_defaults_are_safe():
    p = Profile.from_dict({"id": "p", "subject": "principal",
                           "created_at": "t", "updated_at": "t"})
    assert p.method == "other"
    assert p.content == ""
    assert p.traits == []
    assert p.sources == []


def test_profile_is_immutable():
    p = Profile(id="p", subject="principal", method="mbti", content="",
                traits=[], sources=[], created_at="t", updated_at="t")
    with pytest.raises(AttributeError):
        p.content = "x"  # type: ignore[misc]


# === Goal（A軸データ） ===

def test_goal_round_trip():
    d = {
        "id": "g1", "title": "半年で貯蓄30万円", "category": "money",
        "status": "active", "target_date": "2026-12-01",
        "success_criteria": "普通預金の残高が+30万円",
        "notes": "固定費の見直しから着手",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
        "closed_at": None,
    }
    g = Goal.from_dict(d)
    assert g.category == "money"
    assert g.status == "active"
    assert g.to_dict() == d


def test_goal_rejects_invalid_category():
    with pytest.raises(ValueError):
        Goal(id="g", title="x", category="gambling", status="active",
             target_date=None, success_criteria="", notes="",
             created_at="t", updated_at="t", closed_at=None)


def test_goal_rejects_invalid_status():
    with pytest.raises(ValueError):
        Goal(id="g", title="x", category="money", status="someday",
             target_date=None, success_criteria="", notes="",
             created_at="t", updated_at="t", closed_at=None)


def test_goal_requires_title():
    with pytest.raises(ValueError):
        Goal(id="g", title="", category="money", status="active",
             target_date=None, success_criteria="", notes="",
             created_at="t", updated_at="t", closed_at=None)


def test_goal_defaults_are_safe():
    g = Goal.from_dict({"id": "g", "title": "目標", "created_at": "t", "updated_at": "t"})
    assert g.category == "other"
    assert g.status == "active"
    assert g.target_date is None
    assert g.closed_at is None


# === Step（GOALS の逆算分解） ===

def test_step_round_trip():
    d = {
        "id": "s1", "goal_id": "g1", "title": "固定費一覧を作る", "seq": 1,
        "status": "todo", "due_date": "2026-06-20", "notes": "",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
    }
    s = Step.from_dict(d)
    assert s.goal_id == "g1"
    assert s.seq == 1
    assert s.to_dict() == d


def test_step_requires_goal_id():
    with pytest.raises(ValueError):
        Step(id="s", goal_id="", title="x", seq=1, status="todo",
             due_date=None, notes="", created_at="t", updated_at="t")


def test_step_rejects_invalid_status():
    with pytest.raises(ValueError):
        Step(id="s", goal_id="g", title="x", seq=1, status="waiting",
             due_date=None, notes="", created_at="t", updated_at="t")


def test_step_defaults_are_safe():
    s = Step.from_dict({"id": "s", "goal_id": "g", "title": "x",
                        "created_at": "t", "updated_at": "t"})
    assert s.seq == 0
    assert s.status == "todo"
    assert s.due_date is None


# === derive_role（P×A 役割の決定論導出） ===

def _profile(subject="principal"):
    return {"id": "p", "subject": subject, "method": "mbti", "content": "",
            "traits": [], "sources": [], "created_at": "t", "updated_at": "t"}


def _goal(status="active"):
    return {"id": "g", "title": "x", "category": "money", "status": status,
            "target_date": None, "success_criteria": "", "notes": "",
            "created_at": "t", "updated_at": "t", "closed_at": None}


def test_derive_role_four_quadrants():
    assert derive_role([], []).role == "secretary"
    assert derive_role([_profile()], []).role == "butler"
    assert derive_role([], [_goal()]).role == "coach"
    assert derive_role([_profile()], [_goal()]).role == "anego"


def test_derive_role_exposes_axis_flags():
    rs = derive_role([_profile()], [_goal()])
    assert rs.personalize is True
    assert rs.accompany is True
    rs = derive_role([], [])
    assert rs.personalize is False
    assert rs.accompany is False


def test_derive_role_ignores_non_principal_profiles():
    # 関係者のプロファイルだけでは P は立たない（執事にならない）
    assert derive_role([_profile(subject="u1")], []).role == "secretary"


def test_derive_role_ignores_inactive_goals():
    # 完了・中断した目標だけでは A は立たない（コーチから降りる＝卒業）
    goals = [_goal(status="achieved"), _goal(status="paused"), _goal(status="abandoned")]
    assert derive_role([], goals).role == "secretary"


def test_derive_role_status_round_trip():
    rs = derive_role([_profile()], [])
    assert rs.to_dict() == {"role": "butler", "personalize": True, "accompany": False}
