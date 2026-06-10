"""atomic_io（JSON store 共有の atomic 書込＋破損フォールバック load）のテスト。

write_text_atomic の核心は「publish（os.replace）前に失敗しても旧内容が無傷」——
truncate→write（write_text）の全損経路が存在しないことを monkeypatch で直接検証する。
"""
from __future__ import annotations

import json

import pytest

import adapters.atomic_io as atomic_io
from adapters.atomic_io import load_json_or_default, load_jsonl, write_text_atomic


# --- write_text_atomic ---


def test_write_creates_file_and_parents(tmp_path):
    target = tmp_path / "a" / "b" / "data.json"
    write_text_atomic(target, '{"v": 1}')
    assert target.read_text(encoding="utf-8") == '{"v": 1}'


def test_write_replaces_existing_content(tmp_path):
    target = tmp_path / "data.json"
    write_text_atomic(target, "old")
    write_text_atomic(target, "new")
    assert target.read_text(encoding="utf-8") == "new"


def test_write_leaves_no_tmp_file(tmp_path):
    write_text_atomic(tmp_path / "data.json", "x")
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


def test_write_failure_preserves_old_content(tmp_path, monkeypatch):
    """publish（os.replace）前のクラッシュで旧内容が残る＝truncate→write の全損経路がない。"""
    target = tmp_path / "data.json"
    write_text_atomic(target, "precious")

    def boom(src, dst):
        raise OSError("simulated crash before publish")

    monkeypatch.setattr(atomic_io.os, "replace", boom)
    with pytest.raises(OSError):
        write_text_atomic(target, "half-written")
    assert target.read_text(encoding="utf-8") == "precious"


def test_write_failure_cleans_up_tmp_file(tmp_path, monkeypatch):
    """replace 失敗時に tmp 残骸を残さない（state dir をゴミで汚さない）。"""
    target = tmp_path / "data.json"

    def boom(src, dst):
        raise OSError("simulated crash before publish")

    monkeypatch.setattr(atomic_io.os, "replace", boom)
    with pytest.raises(OSError):
        write_text_atomic(target, "x")
    assert list(tmp_path.iterdir()) == []


def test_write_preserves_japanese(tmp_path):
    target = tmp_path / "j.json"
    write_text_atomic(target, json.dumps({"name": "山田太郎"}, ensure_ascii=False))
    assert "山田太郎" in target.read_text(encoding="utf-8")


# --- load_json_or_default ---


def test_load_missing_file_returns_default(tmp_path):
    result = load_json_or_default(
        tmp_path / "nope.json", parse=lambda d: d, default=lambda: {"d": True}
    )
    assert result == {"d": True}


def test_load_valid_json_is_parsed(tmp_path):
    p = tmp_path / "v.json"
    p.write_text(json.dumps({"value": 42}), encoding="utf-8")
    assert load_json_or_default(p, parse=lambda d: int(d["value"]), default=lambda: 0) == 42


def test_load_corrupt_json_returns_default(tmp_path):
    p = tmp_path / "broken.json"
    p.write_text("{ not json", encoding="utf-8")
    assert load_json_or_default(p, parse=lambda d: d, default=lambda: None) is None


def test_load_parse_error_returns_default(tmp_path):
    """parse 中の KeyError/ValueError も default に倒す（既存 store の catch 集合を踏襲）。"""
    p = tmp_path / "missing-key.json"
    p.write_text("{}", encoding="utf-8")
    assert load_json_or_default(p, parse=lambda d: int(d["value"]), default=lambda: -1) == -1


# --- load_jsonl ---


def test_load_jsonl_missing_file_returns_empty(tmp_path):
    assert load_jsonl(tmp_path / "nope.jsonl", parse_line=lambda d: d) == []


def test_load_jsonl_skips_corrupt_and_blank_lines(tmp_path):
    p = tmp_path / "log.jsonl"
    p.write_text('{"k": 1}\n\n{ broken\n{"k": 2}\n', encoding="utf-8")
    assert load_jsonl(p, parse_line=lambda d: d["k"]) == [1, 2]


def test_load_jsonl_skips_lines_failing_parse(tmp_path):
    """parse_line の KeyError/ValueError も行スキップ（WAL の from_dict 破損と同型）。"""
    p = tmp_path / "log.jsonl"
    p.write_text('{"k": 1}\n{"other": true}\n', encoding="utf-8")
    assert load_jsonl(p, parse_line=lambda d: d["k"]) == [1]
