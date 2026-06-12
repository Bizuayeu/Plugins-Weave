"""P/A 軸 3 テンプレート（PROFILE/GOALS/STEPS）の雛型とコードの乖離防止テスト。

テンプレートは「コピーされない雛型」（説明ドキュメント）だが、_record_schema が
値オブジェクトの実スキーマから乖離すると、雛型を見て実体ファイルを作る利用者を
壊れたレコードへ誘導する。キー集合の一致をテストで張る。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.registry import Goal, Profile, Step

TEMPLATES_DIR = Path(__file__).parents[3] / "templates"

# テンプレ名 -> (records キー, 値オブジェクト, 最小有効レコード)
_NEW_TEMPLATES = {
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
}


@pytest.mark.parametrize("name", _NEW_TEMPLATES)
def test_new_templates_are_valid_json(name):
    """parse 可能で version と空 records 配列（表名キー）を持つ。"""
    data = json.loads((TEMPLATES_DIR / name).read_text(encoding="utf-8"))
    records_key = _NEW_TEMPLATES[name][0]
    assert data["version"] == 1
    assert data[records_key] == []


@pytest.mark.parametrize("name", _NEW_TEMPLATES)
def test_template_schema_matches_value_objects(name):
    """_record_schema のキー集合が値オブジェクト to_dict のキー集合と一致する。"""
    _, record_cls, minimal = _NEW_TEMPLATES[name]
    data = json.loads((TEMPLATES_DIR / name).read_text(encoding="utf-8"))
    schema_keys = set(data["_record_schema"].keys())
    vo_keys = set(record_cls.from_dict(minimal).to_dict().keys())
    assert schema_keys == vo_keys, f"{name}: schema={schema_keys} vs vo={vo_keys}"
