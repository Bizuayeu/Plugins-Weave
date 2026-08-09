from __future__ import annotations

from usecases.orientation import (
    DEFAULT_NOTES_TAIL,
    DEFAULT_TOPIC_WIDTH,
    OrientationService,
    index_knowledge,
    pick_latest_handoffs,
    summarize_task,
    tail_notes,
)

# CLI（Interface）が REGISTRY_SPEC 順で渡す表名。UseCase 側はキー順にセクションを回すだけ
_TABLES = (
    "individuals",
    "tasks",
    "knowledge",
    "abilities",
    "profile",
    "goals",
    "steps",
)


class _FakeLister:
    """RegistryService.list() だけを模す fake（I/O なし＝純ロジックのテスト）。"""

    def __init__(self, records: list[dict]) -> None:
        self._records = records

    def list(self) -> list[dict]:
        return list(self._records)


def _service(sizes: dict[str, int] | None = None, **tables) -> OrientationService:
    listers = {name: _FakeLister(tables.get(name, [])) for name in _TABLES}
    all_sizes = dict.fromkeys(_TABLES, 0)
    all_sizes.update(sizes or {})
    return OrientationService(listers, all_sizes)


def _task(**kw) -> dict:
    base = {
        "id": "T-001",
        "title": "見積を送る",
        "status": "open",
        "priority": "high",
        "due_date": "2026-08-10",
        "requester": "principal",
        "related_individuals": [],
        "notes": "",
        "created_at": "t",
        "updated_at": "t",
        "closed_at": None,
    }
    base.update(kw)
    return base


def _knowledge(**kw) -> dict:
    base = {
        "id": "K-001",
        "topic": "申し送りの置き場",
        "category": "general",
        "content": "",
        "related": [],
        "sources": [],
        "created_at": "t",
        "updated_at": "t",
    }
    base.update(kw)
    return base


# === 空入力: 全セクション見出しが出て counts が 0 ===


def test_empty_tables_render_all_sections_with_zero_counts():
    digest = _service().build()
    for section in (
        "## role",
        "## counts",
        "## tasks",
        "## tasks.notes",
        "## knowledge",
        "## handoff",
    ):
        assert section in digest
    for name in _TABLES:
        assert f"## {name}" in digest
        assert f"{name}: 0 records, 0 bytes" in digest
    assert "0 blocks" in digest


def test_counts_report_records_and_bytes():
    digest = _service(
        sizes={"tasks": 741_000}, tasks=[_task(), _task(id="T-002")]
    ).build()
    assert "tasks: 2 records, 741000 bytes" in digest


def test_role_section_derives_from_profile_and_goals():
    digest = _service(
        profile=[{"id": "pf1", "subject": "principal"}],
        goals=[{"id": "g1", "status": "active"}],
    ).build()
    assert '"role": "anego"' in digest


# === tasks: done の notes は出ない・active の notes は末尾 notes_tail 字に丸まる ===


def test_done_task_notes_absent_from_digest():
    digest = _service(
        tasks=[_task(id="T-001", status="done", notes="DONE_NOTES_MARKER")]
    ).build()
    assert "DONE_NOTES_MARKER" not in digest
    assert "T-001 | done" in digest  # 一行要約には出る


def test_active_task_notes_are_tail_bounded_regardless_of_length():
    """165K 字の notes を持つ active タスクでも digest は notes_tail に有界（沈黙失敗の元を断つ）。"""
    notes = "HEAD_MARKER" + ("x" * 165_000) + "TAIL_MARKER"
    digest = _service(
        tasks=[
            _task(id="T-001", status="in_progress", notes=notes),
            _task(id="T-002", status="done", notes=notes),
        ]
    ).build()
    assert "TAIL_MARKER" in digest
    assert "HEAD_MARKER" not in digest
    # 出力は notes 長に非依存: notes_tail × active 件数 + 定型部（十分な余裕を見た上限）
    assert len(digest) < DEFAULT_NOTES_TAIL + 4_000


def test_notes_tail_option_overrides_default():
    notes = "y" * 10_000
    digest = _service(tasks=[_task(notes=notes)]).build(notes_tail=100)
    assert len(digest) < 2_000


def test_summarize_task_field_order_is_stable():
    line = summarize_task(_task())
    assert line == "T-001 | open | high | 2026-08-10 | 見積を送る"


def test_summarize_task_renders_missing_due_date_as_placeholder():
    assert (
        summarize_task(_task(due_date=None)) == "T-001 | open | high | - | 見積を送る"
    )


def test_tasks_are_sorted_by_id_ascending():
    digest = _service(
        tasks=[_task(id="T-003"), _task(id="T-001"), _task(id="T-002")]
    ).build()
    assert digest.index("T-001 |") < digest.index("T-002 |") < digest.index("T-003 |")


def test_tail_notes_returns_whole_text_when_short():
    assert tail_notes("abc", 10) == "abc"


def test_tail_notes_marks_truncation():
    out = tail_notes("abcdef", 3)
    assert out.endswith("def")
    assert out != "def"  # 切り取られたことが読み手に分かる


def test_non_positive_widths_drop_text_instead_of_passing_it_through():
    """絞るためのオプションが全文を通す穴にならない（`notes[-0:]` は全文になる）。"""
    assert "abc" not in tail_notes("abc", 0)
    assert "abc" not in index_knowledge(_knowledge(topic="abc"), topic_width=0)
    assert pick_latest_handoffs([("a.md", "abc")], latest=1, cap=0)[0][1] != "abc"


# === knowledge: content は出ない・topic は topic_width で切り詰め ===


def test_knowledge_content_absent_and_topic_truncated():
    digest = _service(
        knowledge=[
            _knowledge(id="K-001", topic="z" * 500, content="CONTENT_MARKER"),
        ]
    ).build()
    assert "CONTENT_MARKER" not in digest
    assert "z" * DEFAULT_TOPIC_WIDTH not in digest  # width 超は切り詰められている
    assert "K-001 |" in digest


def test_index_knowledge_truncates_topic_to_width():
    line = index_knowledge(_knowledge(topic="あ" * 300), topic_width=20)
    topic = line.split(" | ", 1)[1]
    assert len(topic) <= 20


def test_topic_width_option_overrides_default():
    digest = _service(knowledge=[_knowledge(topic="w" * 300)]).build(topic_width=10)
    assert "w" * 11 not in digest


# === handoff: ファイル名降順 N 件・各ブロック cap 字 ===


def test_pick_latest_handoffs_selects_newest_by_name_descending():
    blocks = [
        ("20260807T000000Z_s1.md", "a"),
        ("20260809T000000Z_s3.md", "c"),
        ("20260808T000000Z_s2.md", "b"),
    ]
    picked = pick_latest_handoffs(blocks, latest=2, cap=100)
    assert [name for name, _ in picked] == [
        "20260809T000000Z_s3.md",
        "20260808T000000Z_s2.md",
    ]


def test_pick_latest_handoffs_caps_each_block_from_head():
    picked = pick_latest_handoffs([("a.md", "HEAD" + "z" * 10_000)], latest=1, cap=10)
    assert picked[0][1].startswith("HEAD")
    assert len(picked[0][1]) <= 10


def test_pick_latest_handoffs_empty_input_is_noop():
    assert pick_latest_handoffs([], latest=3, cap=8_000) == []


def test_handoff_section_renders_blocks_and_count():
    digest = _service().build(
        handoffs=[("20260809T000000Z_s1.md", "BLOCK_BODY")], handoff_latest=3
    )
    assert "1 blocks" in digest
    assert "20260809T000000Z_s1.md" in digest
    assert "BLOCK_BODY" in digest


def test_handoff_section_respects_latest_and_cap_options():
    blocks = [
        (f"2026080{i}T000000Z_s.md", f"BODY{i}" + "z" * 1_000) for i in range(1, 5)
    ]
    digest = _service().build(handoffs=blocks, handoff_latest=1, handoff_cap=6)
    assert "1 blocks" in digest
    assert "BODY4" in digest  # 最新 1 件のみ、cap 字で丸めて載る
    assert "BODY3" not in digest
    assert "z" * 100 not in digest


# === 後方互換: 既定出力のスナップショット（v1.5.0 と byte 同一） ===

_INDIVIDUAL_RECORD = {
    "uuid": "u1",
    "display_name": "yamada",
    "role": "associate",
    "status": "active",
    "created_at": "t",
    "updated_at": "t",
}

# v1.5.0 実装が既定オプションで出力した digest そのもの。以後の内部整形・オプション追加は
# **この文字列を 1 バイトも動かしてはならない**（起動時オリエンテーションは秘書が毎枠読む
# 契約面であり、既定出力の変化は配布物 Shiori 側の手順書ごと壊す）。
_V150_DEFAULT_DIGEST = """# orientation

## role
{"role": "secretary", "personalize": false, "accompany": false}

## counts
individuals: 1 records, 0 bytes
tasks: 2 records, 0 bytes
knowledge: 2 records, 0 bytes
abilities: 0 records, 0 bytes
profile: 0 records, 0 bytes
goals: 0 records, 0 bytes
steps: 0 records, 0 bytes

## individuals (1 records, full)
[
  {
    "uuid": "u1",
    "display_name": "yamada",
    "role": "associate",
    "status": "active",
    "created_at": "t",
    "updated_at": "t"
  }
]

## tasks (2 records, summary: id | status | priority | due_date | title)
T-001 | open | high | 2026-08-10 | 見積を送る
T-002 | done | low | - | 請求書

## tasks.notes (active only, last 4000 chars)
### T-001
NOTE_A

## knowledge (2 records, index: id | topic)
K-001 | 申し送りの置き場
K-002 | 請求の締め

## abilities (0 records, full)
[]

## profile (0 records, full)
[]

## goals (0 records, full)
[]

## steps (0 records, full)
[]

## handoff (1 blocks, latest 3, cap 8000 chars)
### 20260809T000000Z_s.md
HANDOFF_BODY
"""


def _snapshot_digest(**build_kwargs) -> str:
    return _service(
        individuals=[_INDIVIDUAL_RECORD],
        tasks=[
            _task(notes="NOTE_A"),
            _task(
                id="T-002",
                title="請求書",
                status="done",
                priority="low",
                due_date=None,
                notes="NOTE_B",
            ),
        ],
        knowledge=[
            _knowledge(id="K-001", topic="申し送りの置き場", category="ops"),
            _knowledge(id="K-002", topic="請求の締め", category="billing"),
        ],
    ).build(handoffs=[("20260809T000000Z_s.md", "HANDOFF_BODY")], **build_kwargs)


def test_default_digest_is_byte_identical_to_v150_snapshot():
    """既定出力の同一性契約。オプション追加は既定を変えない（追加のみ・改変なし）。"""
    assert _snapshot_digest() == _V150_DEFAULT_DIGEST


def test_knowledge_category_unset_keeps_v150_snapshot():
    """`knowledge_category` を明示的に None で渡しても既定と同一（後方互換の第二の錠）。"""
    assert _snapshot_digest(knowledge_category=None) == _V150_DEFAULT_DIGEST


# === knowledge の category 絞り（索引 O(n) を母数側から抑える観測オプション） ===


def _categorized_knowledge() -> list[dict]:
    return [
        _knowledge(id="K-001", topic="申し送りの置き場", category="ops"),
        _knowledge(id="K-002", topic="請求の締め", category="billing"),
        _knowledge(id="K-003", topic="定例の段取り", category="ops"),
        _knowledge(id="K-004", topic="与信の見方", category="billing"),
        _knowledge(id="K-005", topic="鍵の預かり", category="general"),
    ]


def test_knowledge_category_filters_rows_and_reports_hidden_count():
    """絞り込み時は該当行だけを出し、見出しの `N of M` で「見えなくなった件数」を残す。"""
    digest = _service(knowledge=_categorized_knowledge()).build(
        knowledge_category="ops"
    )
    assert "## knowledge (2 of 5 records, category=ops, index: id | topic)" in digest
    assert "K-001 |" in digest and "K-003 |" in digest
    for hidden in ("K-002 |", "K-004 |", "K-005 |"):
        assert hidden not in digest


def test_knowledge_category_matches_exactly_not_by_prefix():
    """完全一致——`op` で `ops` を引っ掛けない（絞りの意味が曖昧になる）。"""
    digest = _service(knowledge=_categorized_knowledge()).build(knowledge_category="op")
    assert "## knowledge (0 of 5 records, category=op, index: id | topic)" in digest


def test_unknown_knowledge_category_yields_zero_rows_without_error():
    """存在しない category は 0 行＋見出しのみ。絞りは観測であって検証ではない（エラーにしない）。"""
    digest = _service(knowledge=_categorized_knowledge()).build(
        knowledge_category="nonexistent"
    )
    assert (
        "## knowledge (0 of 5 records, category=nonexistent, index: id | topic)"
        in digest
    )
    assert "K-00" not in digest


def test_knowledge_category_preserves_id_ascending_order():
    digest = _service(knowledge=list(reversed(_categorized_knowledge()))).build(
        knowledge_category="billing"
    )
    assert digest.index("K-002 |") < digest.index("K-004 |")


def test_knowledge_category_does_not_affect_other_sections():
    """絞りは knowledge セクション限定（counts は表の実件数のまま＝母数を隠さない）。"""
    digest = _service(knowledge=_categorized_knowledge(), tasks=[_task()]).build(
        knowledge_category="ops"
    )
    assert "knowledge: 5 records, 0 bytes" in digest
    assert "T-001 |" in digest
