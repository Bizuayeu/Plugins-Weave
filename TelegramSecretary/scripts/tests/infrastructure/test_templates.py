"""雛型とコードの乖離防止テスト（PROFILE/GOALS/STEPS/KNOWLEDGE/SUBJECTS）。

テンプレートは「コピーされない雛型」（説明ドキュメント）だが、_record_schema が
値オブジェクトの実スキーマから乖離すると、雛型を見て実体ファイルを作る利用者を
壊れたレコードへ誘導する。キー集合の一致をテストで張る。

対象は P/A 軸 3 表から始まったが、未カバーの表は乖離しても誰も気づかない——実際
KNOWLEDGE の雛型は `subjects` の追加（v1.9.0）に追従しないまま通っていた。表が増える
たびにここへ 1 行足す（雛型を持つ表はすべてこの網に入れる）。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from domain.registry import Goal, Knowledge, Profile, Step, Subject

TEMPLATES_DIR = Path(__file__).parents[3] / "templates"

# テンプレ名 -> (records キー, 値オブジェクト, 最小有効レコード)
_TEMPLATES = {
    "PROFILE.template.json": (
        "profile",
        Profile,
        {"id": "p", "subject": "principal", "created_at": "t", "updated_at": "t"},
    ),
    "GOALS.template.json": (
        "goals",
        Goal,
        {"id": "g", "title": "x", "created_at": "t", "updated_at": "t"},
    ),
    "STEPS.template.json": (
        "steps",
        Step,
        {"id": "s", "goal_id": "g", "title": "x", "created_at": "t", "updated_at": "t"},
    ),
    "KNOWLEDGE.template.json": (
        "knowledge",
        Knowledge,
        {
            "id": "k",
            "topic": "x",
            "category": "observation",
            "created_at": "t",
            "updated_at": "t",
        },
    ),
    "SUBJECTS.template.json": (
        "subjects",
        Subject,
        {"id": "馬", "created_at": "t", "updated_at": "t"},
    ),
}


@pytest.mark.parametrize("name", _TEMPLATES)
def test_templates_are_valid_json(name):
    """parse 可能で version と空 records 配列（表名キー）を持つ。"""
    data = json.loads((TEMPLATES_DIR / name).read_text(encoding="utf-8"))
    records_key = _TEMPLATES[name][0]
    assert data["version"] == 1
    assert data[records_key] == []


@pytest.mark.parametrize("name", _TEMPLATES)
def test_template_schema_matches_value_objects(name):
    """_record_schema のキー集合が値オブジェクト to_dict のキー集合と一致する。"""
    _, record_cls, minimal = _TEMPLATES[name]
    data = json.loads((TEMPLATES_DIR / name).read_text(encoding="utf-8"))
    schema_keys = set(data["_record_schema"].keys())
    vo_keys = set(record_cls.from_dict(minimal).to_dict().keys())
    assert schema_keys == vo_keys, f"{name}: schema={schema_keys} vs vo={vo_keys}"
