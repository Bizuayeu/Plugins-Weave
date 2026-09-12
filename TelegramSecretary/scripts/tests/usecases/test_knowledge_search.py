"""knowledge search の純関数（I/O なし）。"""

from __future__ import annotations

from usecases.knowledge_search import search_knowledge


def _k(id: str, topic: str = "", content: str = "", subjects: list[str] | None = None):
    return {
        "id": id,
        "topic": topic,
        "category": "method",
        "subjects": subjects or [],
        "content": content,
        "related": [],
        "sources": [],
        "created_at": "t",
        "updated_at": "t",
    }


ROWS = [
    _k("K-001", topic="気学の配点", content="比和ではなく配点で読む"),
    _k("K-002", topic="台帳の先頭は腐る", content="追記式の台帳は…", subjects=["馬"]),
    _k("K-003", topic="ＬＬＭの器", content="Weights are build artifacts"),
]


def test_search_matches_substring_in_content_not_only_topic():
    hits = search_knowledge(ROWS, ["比和"])
    assert [r["id"] for r in hits] == ["K-001"]


def test_search_matches_id_and_subjects_too():
    assert [r["id"] for r in search_knowledge(ROWS, ["k-002"])] == ["K-002"]
    assert [r["id"] for r in search_knowledge(ROWS, ["馬"])] == ["K-002"]


def test_search_is_case_insensitive_and_nfkc_normalized():
    """「ＬＬＭ」と「llm」を別語にすると既出照合が表記揺れで空振りし、重複を焼く側に倒れる。"""
    assert [r["id"] for r in search_knowledge(ROWS, ["llm"])] == ["K-003"]
    assert [r["id"] for r in search_knowledge(ROWS, ["ＷＥＩＧＨＴＳ"])] == ["K-003"]


def test_search_all_terms_must_match_by_default():
    assert [r["id"] for r in search_knowledge(ROWS, ["気学", "配点"])] == ["K-001"]
    assert search_knowledge(ROWS, ["気学", "台帳"]) == []


def test_search_any_term_matches_when_match_all_is_false():
    hits = search_knowledge(ROWS, ["気学", "台帳"], match_all=False)
    assert [r["id"] for r in hits] == ["K-001", "K-002"]


def test_search_with_no_usable_term_returns_nothing_not_everything():
    """空の語で全件一致にすると、絞る口が全通しの穴になる。"""
    assert search_knowledge(ROWS, []) == []
    assert search_knowledge(ROWS, ["", "  "]) == []


def test_search_returns_copies_in_input_order():
    hits = search_knowledge(ROWS, ["の"])
    assert [r["id"] for r in hits] == ["K-001", "K-002", "K-003"]
    hits[0]["topic"] = "mutated"
    assert ROWS[0]["topic"] == "気学の配点"
