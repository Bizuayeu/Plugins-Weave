from __future__ import annotations

from usecases.orientation import (
    DEFAULT_NOTES_TAIL,
    DEFAULT_TOPIC_WIDTH,
    TRUNCATION_MARK,
    OrientationService,
    _truncate,
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
    out = tail_notes("abcdef", 6)  # 幅 6B のうち 3B はマーカーが占める
    assert out.endswith("def")
    assert out != "def"  # 切り取られたことが読み手に分かる


def test_non_positive_widths_drop_text_instead_of_passing_it_through():
    """絞るためのオプションが全文を通す穴にならない（`notes[-0:]` は全文になる）。"""
    assert "abc" not in tail_notes("abc", 0)
    assert "abc" not in index_knowledge(_knowledge(topic="abc"), topic_width=0)
    assert pick_latest_handoffs([("a.md", "abc")], latest=1, cap=0)[0][1] != "abc"


# === 丸めの単位は UTF-8 バイト（v1.7.0 単位是正） ===

_MARK_BYTES = len(TRUNCATION_MARK.encode("utf-8"))  # マーカーも幅の内側に置く（3B）


def _utf8_len(text: str) -> int:
    return len(text.encode("utf-8"))


def _char_counted_truncate(text: str, width: int) -> str:
    """同じ丸め規約を字数（`len()`）で数えた参照実装（1 字＝1 バイトの世界）。"""
    if width <= 0:
        return TRUNCATION_MARK
    if len(text) <= width:
        return text
    return text[: max(width - _MARK_BYTES, 0)] + TRUNCATION_MARK


def _char_counted_tail(text: str, width: int) -> str:
    """`tail_notes` の丸め規約を字数で数えた参照実装（末尾を残す側）。"""
    if width <= 0:
        return TRUNCATION_MARK
    if len(text) <= width:
        return text
    body = max(width - _MARK_BYTES, 0)
    return TRUNCATION_MARK + (text[-body:] if body else "")


def test_truncate_bounds_japanese_topic_by_utf8_bytes_without_splitting_characters():
    """日本語 100 字の topic を幅 120 で丸めると 120 バイト以内に収まる。

    字数で数えていた v1.5.0 では日本語 1 字≈2.47 バイトの分だけ実効幅が膨らみ、
    出力が persisted-output へ退避される沈黙失敗に効いていた。上限（退避閾値）と
    同じ単位で数えて初めて有界性が言える。丸めは文字境界で止める（字を割らない）。
    """
    out = _truncate("あ" * 100, 120)
    assert _utf8_len(out) <= 120
    assert out.endswith(TRUNCATION_MARK)
    assert set(out[: -len(TRUNCATION_MARK)]) == {"あ"}  # 途中で割れた字が無い
    assert _utf8_len(out + "あ") > 120  # 収まる限りは詰める（切り過ぎない）


def test_tail_notes_bounds_japanese_notes_by_utf8_bytes_keeping_the_tail():
    """日本語混在の長文 notes も末尾側をバイトで数えて残す（申し送りは末尾に堆積する）。"""
    notes = "捨てられる頭" * 500 + "TAIL_MARKER"
    out = tail_notes(notes, 4_000)
    assert _utf8_len(out) <= 4_000
    assert out.startswith(TRUNCATION_MARK)
    assert out.endswith("TAIL_MARKER")


def test_ascii_rounding_is_identical_whether_counted_in_bytes_or_characters():
    """ASCII だけの入力では字数＝バイト数——単位是正の前後で結果が変わらない退行錠。

    日本語で縮む一方、英数字主体の運用は従来と同じ丸めを受け続ける（縮小の影響範囲を
    「1 字が 1 バイトを超える入力」に限定できていることの確認）。
    """
    for width in (0, 1, 5, 10, 120):
        for text in ("", "a", "abcdef", "x" * 300):
            assert _truncate(text, width) == _char_counted_truncate(text, width)
            assert tail_notes(text, width) == _char_counted_tail(text, width)


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
    digest = _service().build(handoffs=blocks, handoff_latest=1, handoff_cap=8)
    assert "1 blocks" in digest
    assert "BODY4" in digest  # 最新 1 件のみ、cap 8B（本文 5B＋マーカー 3B）で載る
    assert "BODY3" not in digest
    assert "z" * 100 not in digest


# === 後方互換: 既定出力のスナップショット（幅内入力は単位変更の影響を受けない） ===

_INDIVIDUAL_RECORD = {
    "uuid": "u1",
    "display_name": "yamada",
    "role": "associate",
    "status": "active",
    "created_at": "t",
    "updated_at": "t",
}

# v1.5.0 実装が既定オプションで出力した digest。以後の内部整形・オプション追加は
# **この文字列を 1 バイトも動かしてはならない**（起動時オリエンテーションは秘書が毎枠読む
# 契約面であり、既定出力の変化は配布物 Shiori 側の手順書ごと壊す）。v1.7.0 の単位是正で
# 動いたのは見出しの単位表記（chars → bytes）だけ——本文は幅内入力ゆえ v1.5.0 と同一。
_DEFAULT_DIGEST_SNAPSHOT = """# orientation

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

## tasks.notes (active only, last 4000 bytes)
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

## handoff (1 blocks, latest 3, cap 8000 bytes)
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


def test_default_digest_keeps_v150_body_for_inputs_within_the_width():
    """既定出力の同一性契約。幅内に収まる入力は chars → bytes の単位是正を受けない。

    オプション追加も単位是正も既定出力の本文を変えない（動くのは見出しの単位表記のみ）。
    縮むのは「1 字が 1 バイトを超える入力が幅を超えたとき」に限られる、という境界の宣言。
    """
    assert _snapshot_digest() == _DEFAULT_DIGEST_SNAPSHOT


def test_knowledge_category_unset_keeps_the_default_snapshot():
    """`knowledge_category` を明示的に None で渡しても既定と同一（後方互換の第二の錠）。"""
    assert _snapshot_digest(knowledge_category=None) == _DEFAULT_DIGEST_SNAPSHOT


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


# === knowledge の latest 絞り（索引の行数を新しい順で頭打ちにする、v1.7.0 Stage 3） ===


def test_knowledge_latest_keeps_the_newest_ids_and_discloses_the_total():
    """新しい順 N 件だけを索引に残し、見出しの `latest N of M` で母数を開示する。

    id は日付順に振られるため「id の大きい方が新しい」——選び方は handoff（名前降順）と
    同じ読み筋。表示順は昇順のまま（絞りは母数を減らす観測であって、索引の読み方は変えない）。
    """
    digest = _service(knowledge=_categorized_knowledge()).build(knowledge_latest=2)
    assert (
        "## knowledge (latest 2 of 5 records, newest last, index: id | topic)" in digest
    )
    assert digest.index("K-004 |") < digest.index("K-005 |")
    for dropped in ("K-001 |", "K-002 |", "K-003 |"):
        assert dropped not in digest


def test_knowledge_latest_unset_keeps_the_default_snapshot():
    """`knowledge_latest` を明示的に None で渡しても既定と同一（後方互換の第三の錠）。"""
    assert _snapshot_digest(knowledge_latest=None) == _DEFAULT_DIGEST_SNAPSHOT


def test_zero_knowledge_latest_empties_the_index_instead_of_passing_all_rows():
    """`0` は「1 件も載せない」端点（Stage 1 の端点規約と同調）。

    `rows[-0:]` は全件に化ける——絞るための指定が全通しの穴になる罠を、`tail_notes` と
    同じ理由でここでも塞ぐ。見出しは 0 件でも `of M` を残し、隠れた件数を開示する。
    """
    digest = _service(knowledge=_categorized_knowledge()).build(knowledge_latest=0)
    assert (
        "## knowledge (latest 0 of 5 records, newest last, index: id | topic)" in digest
    )
    assert "K-00" not in digest


def test_knowledge_latest_applies_after_the_category_filter():
    """category → latest の順で効き、母数 M は category 絞り後の件数になる。

    順序が逆だと「新しい N 件の中に該当 category が無ければ 0 件」という、絞り込みの
    意味が壊れた結果になる。
    """
    digest = _service(knowledge=_categorized_knowledge()).build(
        knowledge_category="ops", knowledge_latest=1
    )
    assert (
        "## knowledge (latest 1 of 2 records, newest last, category=ops, "
        "index: id | topic)" in digest
    )
    assert "K-003 |" in digest  # ops のうち新しい方
    assert "K-001 |" not in digest


def test_newest_last_is_disclosed_only_when_latest_is_set():
    """読み方の開示 `newest last` は latest 指定時だけ載る。

    「選ぶのは新しい順、並びは id 昇順」という捻れを、末尾が最新と読ませて解く注記——
    絞っていない索引に付けると、全件が新しい順に並んでいるかのような誤読を生む。
    """
    rows = _categorized_knowledge()
    assert "newest last" in _service(knowledge=rows).build(knowledge_latest=2)
    assert "newest last" not in _service(knowledge=rows).build()
    assert "newest last" not in _service(knowledge=rows).build(knowledge_category="ops")
