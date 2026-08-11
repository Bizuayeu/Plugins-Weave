from __future__ import annotations

import pytest
from domain.registry import Ability, Identity, Individual, Knowledge, Task

# === Individual / Identity ===


def test_individual_round_trip():
    d = {
        "uuid": "u1",
        "display_name": "山田太郎",
        "role": "associate",
        "status": "active",
        "telegram_chat_id": 100,
        "line_user_id": None,
        "identity": {
            "category": "client",
            "relationship_label": "営業部長",
            "honorific": "山田さん",
            "tone": "polite",
            "context_notes": "",
            "priority_bias": "normal",
            "taboo_topics": [],
            "shared_with": [],
        },
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    ind = Individual.from_dict(d)
    assert ind.uuid == "u1"
    assert ind.identity.tone == "polite"
    assert ind.to_dict() == d


def test_individual_rejects_invalid_role():
    with pytest.raises(ValueError):
        Individual(
            uuid="u",
            display_name="x",
            role="boss",
            status="active",
            telegram_chat_id=None,
            line_user_id=None,
            identity=Identity(),
            created_at="t",
            updated_at="t",
        )


def test_individual_rejects_invalid_status():
    with pytest.raises(ValueError):
        Individual(
            uuid="u",
            display_name="x",
            role="associate",
            status="unknown",
            telegram_chat_id=None,
            line_user_id=None,
            identity=Identity(),
            created_at="t",
            updated_at="t",
        )


def test_identity_rejects_invalid_tone():
    with pytest.raises(ValueError):
        Identity(tone="shouting")


def test_identity_defaults_are_safe():
    i = Identity()
    assert i.taboo_topics == []
    assert i.shared_with == []
    assert i.tone == "polite"


def test_individual_is_immutable():
    ind = Individual(
        uuid="u",
        display_name="x",
        role="associate",
        status="active",
        telegram_chat_id=None,
        line_user_id=None,
        identity=Identity(),
        created_at="t",
        updated_at="t",
    )
    with pytest.raises(AttributeError):
        ind.status = "blocked"  # type: ignore[misc]


# === Task ===


def test_task_round_trip():
    d = {
        "id": "t1",
        "title": "見積依頼",
        "status": "open",
        "priority": "high",
        "due_date": "2026-06-01",
        "requester": "principal",
        "related_individuals": ["u1"],
        "notes": "",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "closed_at": None,
    }
    t = Task.from_dict(d)
    assert t.id == "t1"
    assert t.status == "open"
    assert t.to_dict() == d


def test_task_rejects_invalid_status():
    with pytest.raises(ValueError):
        Task(
            id="t",
            title="x",
            status="paused",
            priority="normal",
            due_date=None,
            requester="principal",
            related_individuals=[],
            notes="",
            created_at="t",
            updated_at="t",
            closed_at=None,
        )


def test_task_rejects_invalid_priority():
    with pytest.raises(ValueError):
        Task(
            id="t",
            title="x",
            status="open",
            priority="urgent",
            due_date=None,
            requester="principal",
            related_individuals=[],
            notes="",
            created_at="t",
            updated_at="t",
            closed_at=None,
        )


# === Knowledge ===


def test_knowledge_round_trip():
    d = {
        "id": "k1",
        "topic": "決済フロー",
        "category": "method",
        "subjects": [],
        "content": "判断と理由",
        "related": [],
        "sources": ["t1", "log-ref-1"],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    k = Knowledge.from_dict(d)
    assert k.topic == "決済フロー"
    assert k.category == "method"
    assert k.to_dict() == d


def test_knowledge_requires_topic():
    with pytest.raises(ValueError):
        Knowledge(
            id="k",
            topic="",
            category="observation",
            subjects=[],
            content="x",
            related=[],
            sources=[],
            created_at="t",
            updated_at="t",
        )


# 許可集合の SSoT は移行完了報告（handoff 20260809T143056Z §1.5）。テスト側は
# 実装定数を import せず literal で持つ（定数を写すだけの同語反復にしないため）。
_ALLOWED_KNOWLEDGE_CATEGORIES = [
    "observation",
    "research",
    "harness",
    "domain-insight",
    "analysis",
    "design",
    "method",
    "philosophy",
    "business",
    "decision",
]


def test_knowledge_rejects_invalid_category():
    with pytest.raises(ValueError) as exc:
        Knowledge(
            id="k",
            topic="x",
            category="ops",
            subjects=[],
            content="",
            related=[],
            sources=[],
            created_at="t",
            updated_at="t",
        )
    # 弾かれる主体が自走エージェントなので、エラー文だけで選び直せる情報量を持たせる
    message = str(exc.value)
    for allowed in _ALLOWED_KNOWLEDGE_CATEGORIES:
        assert allowed in message


@pytest.mark.parametrize("category", _ALLOWED_KNOWLEDGE_CATEGORIES)
def test_knowledge_accepts_every_allowed_category(category):
    d = {
        "id": "k1",
        "topic": "決済フロー",
        "category": category,
        "subjects": [],
        "content": "判断と理由",
        "related": [],
        "sources": [],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    assert Knowledge.from_dict(d).to_dict() == d


def test_knowledge_carries_subjects_through_round_trip():
    # 主題軸（category と直交する引き出し軸）。固定キー転記だった頃は
    # from_dict が subjects を落とし、add が exit 0 のまま沈黙消滅していた
    d = {
        "id": "k1",
        "topic": "厩舎の動線",
        "category": "domain-insight",
        "subjects": ["馬", "建設"],
        "content": "",
        "related": [],
        "sources": [],
        "created_at": "t",
        "updated_at": "t",
    }
    k = Knowledge.from_dict(d)
    assert k.subjects == ["馬", "建設"]
    assert k.to_dict()["subjects"] == ["馬", "建設"]


def test_knowledge_subjects_default_to_empty():
    # subjects を持たない既存レコードの読み出しを壊さない（後方互換）
    k = Knowledge.from_dict(
        {
            "id": "k1",
            "topic": "x",
            "category": "method",
            "created_at": "t",
            "updated_at": "t",
        }
    )
    assert k.subjects == []


def test_knowledge_from_dict_requires_category():
    # 暗黙 default（"general"）は許可集合に無い値を沈黙生成する fail-open だった
    with pytest.raises(KeyError):
        Knowledge.from_dict(
            {
                "id": "k1",
                "topic": "決済フロー",
                "created_at": "t",
                "updated_at": "t",
            }
        )


# === Subject（主題軸の語彙、開いた語彙＝データ側） ===

from domain.registry import Subject

# 主題語彙のサンプル。実体は SUBJECTS テーブル（データ）なので、テストは
# seed 語彙としてだけ持つ——コード側の定数ではない（category との対比が設計核）
_SEED_SUBJECT_IDS = {
    "馬",
    "建設",
    "製造",
    "経営",
    "AI業界",
    "ハーネス",
    "方法論",
    "哲学",
    "農",
}
_ALLOWED_SUBJECT_STATUSES = ["active", "deprecated"]


def test_subject_round_trip():
    d = {
        "id": "馬",
        "label": "馬",
        "aliases": ["horse", "馬事"],
        "status": "active",
        "note": "厩舎・馬術・馬産の話題",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    s = Subject.from_dict(d)
    assert s.id == "馬"
    assert s.aliases == ["horse", "馬事"]
    assert s.to_dict() == d


def test_subject_rejects_invalid_status():
    with pytest.raises(ValueError) as exc:
        Subject(
            id="馬",
            label="馬",
            aliases=[],
            status="retired",
            note="",
            created_at="t",
            updated_at="t",
        )
    # Knowledge category と同じ方針——弾かれる主体が自走エージェントなので許可値を列挙する
    message = str(exc.value)
    for allowed in _ALLOWED_SUBJECT_STATUSES:
        assert allowed in message


def test_subject_requires_id():
    # id は照合キー（正準 slug）。空 id は語彙として引けない
    with pytest.raises(ValueError):
        Subject(
            id="",
            label="馬",
            aliases=[],
            status="active",
            note="",
            created_at="t",
            updated_at="t",
        )


def test_subject_defaults_are_safe():
    s = Subject.from_dict({"id": "農", "created_at": "t", "updated_at": "t"})
    assert s.label == ""
    assert s.aliases == []
    assert s.status == "active"
    assert s.note == ""


def test_subject_accepts_deprecated_status():
    # 廃止は削除ではない——既存レコードの読み出しを壊さず新規付与だけを止める
    s = Subject.from_dict(
        {"id": "旧語", "status": "deprecated", "created_at": "t", "updated_at": "t"}
    )
    assert s.status == "deprecated"


# === Ability ===


def test_ability_round_trip():
    d = {
        "id": "fortune-telling",
        "name": "占術鑑定",
        "trigger": "占い・鑑定・姓名判断・易・タロット・人物リーディング",
        "skill_path": "base-repo/skills/fortune-telling",
        "guidance": "占い依頼を受けたら SKILL.md を読み、鑑定書を生成して返す",
        "related": ["knowledge-id-1"],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    a = Ability.from_dict(d)
    assert a.id == "fortune-telling"
    assert a.name == "占術鑑定"
    assert a.skill_path == "base-repo/skills/fortune-telling"
    assert a.to_dict() == d


def test_ability_requires_name():
    with pytest.raises(ValueError):
        Ability(
            id="a",
            name="",
            trigger="x",
            skill_path="p",
            guidance="g",
            related=[],
            created_at="t",
            updated_at="t",
        )


def test_ability_defaults_are_safe():
    a = Ability.from_dict(
        {"id": "a", "name": "占い", "created_at": "t", "updated_at": "t"}
    )
    assert a.trigger == ""
    assert a.skill_path == ""
    assert a.guidance == ""
    assert a.related == []


def test_ability_is_immutable():
    a = Ability(
        id="a",
        name="x",
        trigger="",
        skill_path="",
        guidance="",
        related=[],
        created_at="t",
        updated_at="t",
    )
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
        "id": "p1",
        "subject": "principal",
        "method": "mbti",
        "content": "INTJ。長期計画を好み、締切前倒しの段取りが響く",
        "traits": ["計画的", "内省的"],
        "sources": ["対話 2026-06-12"],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    p = Profile.from_dict(d)
    assert p.subject == "principal"
    assert p.method == "mbti"
    assert p.to_dict() == d


def test_profile_rejects_invalid_method():
    with pytest.raises(ValueError):
        Profile(
            id="p",
            subject="principal",
            method="palm_reading",
            content="",
            traits=[],
            sources=[],
            created_at="t",
            updated_at="t",
        )


def test_profile_requires_subject():
    with pytest.raises(ValueError):
        Profile(
            id="p",
            subject="",
            method="mbti",
            content="",
            traits=[],
            sources=[],
            created_at="t",
            updated_at="t",
        )


def test_profile_defaults_are_safe():
    p = Profile.from_dict(
        {"id": "p", "subject": "principal", "created_at": "t", "updated_at": "t"}
    )
    assert p.method == "other"
    assert p.content == ""
    assert p.traits == []
    assert p.sources == []


def test_profile_is_immutable():
    p = Profile(
        id="p",
        subject="principal",
        method="mbti",
        content="",
        traits=[],
        sources=[],
        created_at="t",
        updated_at="t",
    )
    with pytest.raises(AttributeError):
        p.content = "x"  # type: ignore[misc]


# === Goal（A軸データ） ===


def test_goal_round_trip():
    d = {
        "id": "g1",
        "title": "半年で貯蓄30万円",
        "category": "money",
        "status": "active",
        "target_date": "2026-12-01",
        "success_criteria": "普通預金の残高が+30万円",
        "notes": "固定費の見直しから着手",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "closed_at": None,
    }
    g = Goal.from_dict(d)
    assert g.category == "money"
    assert g.status == "active"
    assert g.to_dict() == d


def test_goal_rejects_invalid_category():
    with pytest.raises(ValueError):
        Goal(
            id="g",
            title="x",
            category="gambling",
            status="active",
            target_date=None,
            success_criteria="",
            notes="",
            created_at="t",
            updated_at="t",
            closed_at=None,
        )


def test_goal_rejects_invalid_status():
    with pytest.raises(ValueError):
        Goal(
            id="g",
            title="x",
            category="money",
            status="someday",
            target_date=None,
            success_criteria="",
            notes="",
            created_at="t",
            updated_at="t",
            closed_at=None,
        )


def test_goal_requires_title():
    with pytest.raises(ValueError):
        Goal(
            id="g",
            title="",
            category="money",
            status="active",
            target_date=None,
            success_criteria="",
            notes="",
            created_at="t",
            updated_at="t",
            closed_at=None,
        )


def test_goal_defaults_are_safe():
    g = Goal.from_dict(
        {"id": "g", "title": "目標", "created_at": "t", "updated_at": "t"}
    )
    assert g.category == "other"
    assert g.status == "active"
    assert g.target_date is None
    assert g.closed_at is None


# === Step（GOALS の逆算分解） ===


def test_step_round_trip():
    d = {
        "id": "s1",
        "goal_id": "g1",
        "title": "固定費一覧を作る",
        "seq": 1,
        "status": "todo",
        "due_date": "2026-06-20",
        "notes": "",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    s = Step.from_dict(d)
    assert s.goal_id == "g1"
    assert s.seq == 1
    assert s.to_dict() == d


def test_step_requires_goal_id():
    with pytest.raises(ValueError):
        Step(
            id="s",
            goal_id="",
            title="x",
            seq=1,
            status="todo",
            due_date=None,
            notes="",
            created_at="t",
            updated_at="t",
        )


def test_step_rejects_invalid_status():
    with pytest.raises(ValueError):
        Step(
            id="s",
            goal_id="g",
            title="x",
            seq=1,
            status="waiting",
            due_date=None,
            notes="",
            created_at="t",
            updated_at="t",
        )


def test_step_defaults_are_safe():
    s = Step.from_dict(
        {"id": "s", "goal_id": "g", "title": "x", "created_at": "t", "updated_at": "t"}
    )
    assert s.seq == 0
    assert s.status == "todo"
    assert s.due_date is None


# === derive_role（P×A 役割の決定論導出） ===


def _profile(subject="principal"):
    return {
        "id": "p",
        "subject": subject,
        "method": "mbti",
        "content": "",
        "traits": [],
        "sources": [],
        "created_at": "t",
        "updated_at": "t",
    }


def _goal(status="active"):
    return {
        "id": "g",
        "title": "x",
        "category": "money",
        "status": status,
        "target_date": None,
        "success_criteria": "",
        "notes": "",
        "created_at": "t",
        "updated_at": "t",
        "closed_at": None,
    }


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
    goals = [
        _goal(status="achieved"),
        _goal(status="paused"),
        _goal(status="abandoned"),
    ]
    assert derive_role([], goals).role == "secretary"


def test_derive_role_status_round_trip():
    rs = derive_role([_profile()], [])
    assert rs.to_dict() == {"role": "butler", "personalize": True, "accompany": False}


# === 未知キー検出・主題語彙照合（純関数） ===

from domain.registry import invalid_subjects, unknown_keys


def _knowledge_raw(**extra):
    d = {
        "id": "k1",
        "topic": "x",
        "category": "method",
        "subjects": [],
        "content": "",
        "related": [],
        "sources": [],
        "created_at": "t",
        "updated_at": "t",
    }
    d.update(extra)
    return d


def test_unknown_keys_catches_typo():
    # 単数形の typo は from_dict では沈黙して消える。ここで拾えることが fail-closed の前提
    raw = _knowledge_raw(subject=["馬"])
    del raw["subjects"]
    assert unknown_keys(Knowledge, raw) == {"subject"}


def test_unknown_keys_is_empty_for_known_keys_only():
    assert unknown_keys(Knowledge, _knowledge_raw()) == set()


def test_unknown_keys_allows_omitted_keys():
    # 「未知」であって「不足」ではない——省略可能フィールドの欠落は検出対象外
    assert (
        unknown_keys(Knowledge, {"id": "k1", "topic": "x", "category": "method"})
        == set()
    )


def test_unknown_keys_does_not_inspect_nested_dicts():
    # トップレベルのみ（沈黙消滅の実害はトップレベルで起きた）。ネストは実害が出たら広げる
    raw = {
        "uuid": "u1",
        "display_name": "x",
        "role": "associate",
        "status": "active",
        "identity": {"tone": "polite", "bogus": 1},
        "created_at": "t",
        "updated_at": "t",
    }
    assert unknown_keys(Individual, raw) == set()


def test_invalid_subjects_returns_out_of_vocabulary_terms():
    assert invalid_subjects(["馬", "宇宙"], _SEED_SUBJECT_IDS) == ["宇宙"]


def test_invalid_subjects_is_empty_when_all_in_vocabulary():
    assert invalid_subjects(["馬", "建設", "農"], _SEED_SUBJECT_IDS) == []


def test_invalid_subjects_preserves_input_order():
    # エラー文にそのまま並べる想定なので、秘書が渡した順で返す
    assert invalid_subjects(["宇宙", "馬", "深海"], _SEED_SUBJECT_IDS) == [
        "宇宙",
        "深海",
    ]


def test_invalid_subjects_rejects_everything_when_vocabulary_is_empty():
    # SUBJECTS 未投入（active 0 件）の間は主題付与が全て弾かれる＝語彙先行の運用順
    assert invalid_subjects(["馬"], set()) == ["馬"]
