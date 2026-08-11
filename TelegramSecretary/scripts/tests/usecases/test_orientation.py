from __future__ import annotations

import json

from usecases.orientation import (
    DEFAULT_NOTES_TAIL,
    DEFAULT_TOPIC_WIDTH,
    TRUNCATION_MARK,
    OrientationService,
    _truncate,
    cap_record_field,
    index_knowledge,
    pick_latest_handoffs,
    summarize_task,
    tail_notes,
)

# CLI（Interface）が REGISTRY_SPEC 順で渡す表名。UseCase 側はキー順にセクションを回すだけ
# （並びは REGISTRY_SPEC が SSoT——8 表目 subjects は knowledge の直後）
_TABLES = (
    "individuals",
    "tasks",
    "knowledge",
    "subjects",
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
    topic = line.split(" | ")[2]
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
# v1.9.0 Stage 3 で knowledge 索引が `id | subjects | topic` の 3 列になり、この契約面を
# **意図的に**動かした（大環主裁可 Q5「索引併記する」）。オプション追加による非破壊とは別枠の
# 仕様変更なので、更新したのはこの 1 セクションだけ——他セクションは 1 バイトも動かさない。
# v1.10.0 Stage 1 で subjects / steps を一行索引へ**意図的に**変えた（同じ別枠扱い）。
# 併せて 8 表目 subjects を `_TABLES` に載せた——REGISTRY_SPEC（SSoT）は v1.9.0 Stage 4 で
# 既に 8 表で、この fixture だけが 7 表のまま取り残されていた。動いたのは counts の 1 行と
# subjects / steps の 2 セクションで、他 6 表は `_UNRELATED_SECTIONS_SNAPSHOT` が固定する。
_DEFAULT_DIGEST_SNAPSHOT = """# orientation

## role
{"role": "secretary", "personalize": false, "accompany": false}

## counts
individuals: 1 records, 0 bytes
tasks: 2 records, 0 bytes
knowledge: 2 records, 0 bytes
subjects: 0 records, 0 bytes
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

## knowledge (2 records, index: id | subjects | topic)
K-001 | - | 申し送りの置き場
K-002 | - | 請求の締め

## subjects (0 records, index: id | label | aliases | status | note)

## abilities (0 records, full)
[]

## profile (0 records, full)
[]

## goals (0 records, full)
[]

## steps (0 records, index: id | goal_id | seq | status | title)

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
    assert (
        "## knowledge (2 of 5 records, category=ops, index: id | subjects | topic)"
        in digest
    )
    assert "K-001 |" in digest and "K-003 |" in digest
    for hidden in ("K-002 |", "K-004 |", "K-005 |"):
        assert hidden not in digest


def test_knowledge_category_matches_exactly_not_by_prefix():
    """完全一致——`op` で `ops` を引っ掛けない（絞りの意味が曖昧になる）。"""
    digest = _service(knowledge=_categorized_knowledge()).build(knowledge_category="op")
    assert (
        "## knowledge (0 of 5 records, category=op, index: id | subjects | topic)"
        in digest
    )


def test_unknown_knowledge_category_yields_zero_rows_without_error():
    """存在しない category は 0 行＋見出しのみ。絞りは観測であって検証ではない（エラーにしない）。"""
    digest = _service(knowledge=_categorized_knowledge()).build(
        knowledge_category="nonexistent"
    )
    assert (
        "## knowledge (0 of 5 records, category=nonexistent, index: id | subjects | topic)"
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
        "## knowledge (latest 2 of 5 records, newest last, index: id | subjects | topic)"
        in digest
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
        "## knowledge (latest 0 of 5 records, newest last, index: id | subjects | topic)"
        in digest
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
        "index: id | subjects | topic)" in digest
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


# === 蓋の無い表への上限ノブ（小表の支配的長文フィールドと tasks 要約件数、v1.9.0 Stage 2） ===


def _profile(**kw) -> dict:
    base = {
        "id": "PF-001",
        "subject": "principal",
        "method": "interview",
        "content": "",
        "traits": [],
        "sources": [],
        "created_at": "t",
        "updated_at": "t",
    }
    base.update(kw)
    return base


def _ability(**kw) -> dict:
    base = {
        "id": "A-001",
        "name": "占術鑑定",
        "trigger": "占い",
        "skill_path": "skills/precognitive-viewer",
        "guidance": "",
        "related": [],
        "created_at": "t",
        "updated_at": "t",
    }
    base.update(kw)
    return base


def _table_json(digest: str, name: str) -> list[dict]:
    """全文セクションの JSON 本文を読み戻す（丸めが構造を壊していないことも同時に見る）。"""
    body = digest.split(f"\n## {name} (", 1)[1].split("\n", 1)[1]
    return json.loads(body.split("\n## ", 1)[0])


def test_profile_cap_bounds_content_and_discloses_the_cap():
    """支配項 content をバイトで丸め、蓋が掛かっている事実を見出しで開示する。

    丸めの規約（バイト・文字境界・マーカーは幅の内側）は `_truncate` のものがそのまま効く
    ——新しい丸め方をここで発明しない。
    """
    digest = _service(profile=[_profile(content="あ" * 500)]).build(profile_cap=100)
    assert "## profile (1 records, full, content cap 100 bytes)" in digest
    content = _table_json(digest, "profile")[0]["content"]
    assert _utf8_len(content) <= 100
    assert content.endswith(TRUNCATION_MARK)


def test_cap_leaves_the_other_fields_of_the_record_intact():
    """丸めるのは支配項 1 つだけ——JSON 構造を壊さない（個票は `get --key` で引ける）。"""
    record = _table_json(
        _service(profile=[_profile(content="z" * 500, traits=["寡黙"])]).build(
            profile_cap=50
        ),
        "profile",
    )[0]
    assert record["id"] == "PF-001"
    assert record["method"] == "interview"
    assert record["traits"] == ["寡黙"]


def test_abilities_cap_bounds_guidance():
    digest = _service(abilities=[_ability(guidance="g" * 500)]).build(abilities_cap=40)
    assert "## abilities (1 records, full, guidance cap 40 bytes)" in digest
    assert _utf8_len(_table_json(digest, "abilities")[0]["guidance"]) <= 40


def test_individuals_cap_bounds_the_nested_context_notes():
    """individuals の支配項は identity 直下——ネストしていても兄弟キーは不変のまま丸める。"""
    record = dict(_INDIVIDUAL_RECORD)
    record["identity"] = {"context_notes": "の" * 300, "taboo_topics": ["政治"]}
    digest = _service(individuals=[record]).build(individuals_cap=60)
    assert (
        "## individuals (1 records, full, identity.context_notes cap 60 bytes)"
        in digest
    )
    identity = _table_json(digest, "individuals")[0]["identity"]
    assert _utf8_len(identity["context_notes"]) <= 60
    assert identity["taboo_topics"] == ["政治"]


def test_cap_is_a_noop_when_the_dominant_field_is_absent():
    """支配項を持たないレコードでも cap 指定で落ちない（表は表のまま出る）。"""
    digest = _service(individuals=[_INDIVIDUAL_RECORD]).build(individuals_cap=10)
    assert _table_json(digest, "individuals")[0] == _INDIVIDUAL_RECORD


def test_zero_profile_cap_leaves_only_the_marker():
    """`0` はマーカーのみ＝falsy-zero 封じ（判定は `is not None`、丸めは `_truncate` の非正規約）。"""
    digest = _service(profile=[_profile(content="CONTENT_MARKER")]).build(profile_cap=0)
    assert "CONTENT_MARKER" not in digest
    assert _table_json(digest, "profile")[0]["content"] == TRUNCATION_MARK
    assert "## profile (1 records, full, content cap 0 bytes)" in digest


def test_cap_record_field_does_not_mutate_the_input_record():
    """lister が返した実体を汚さない（同じ dict を後段が読む可能性を潰す）。"""
    record = _profile(content="x" * 100)
    capped = cap_record_field(record, ("content",), 10)
    assert record["content"] == "x" * 100
    assert _utf8_len(capped["content"]) <= 10


def test_cap_record_field_copies_the_nested_dict_before_capping():
    identity = {"context_notes": "y" * 100}
    capped = cap_record_field({"identity": identity}, ("identity", "context_notes"), 10)
    assert identity["context_notes"] == "y" * 100  # 入れ子も共有しない
    assert _utf8_len(capped["identity"]["context_notes"]) <= 10


def test_tasks_latest_keeps_the_newest_ids_and_discloses_the_total():
    """一行要約を id 昇順の末尾 N 件に絞る（`pick_latest_knowledge` と同じ読み筋）。"""
    digest = _service(
        tasks=[_task(id=f"T-00{i}", notes=f"NOTE_{i}") for i in range(1, 5)]
    ).build(tasks_latest=2)
    assert (
        "## tasks (latest 2 of 4 records, newest last, "
        "summary: id | status | priority | due_date | title)" in digest
    )
    assert digest.index("T-003 |") < digest.index("T-004 |")
    for dropped in ("T-001 |", "T-002 |"):
        assert dropped not in digest


def test_tasks_notes_follow_the_latest_filter():
    """落ちた task の notes は載せない——要約に無い id の申し送りだけが残ると読み手が迷子になる。"""
    digest = _service(
        tasks=[_task(id=f"T-00{i}", notes=f"NOTE_{i}") for i in range(1, 5)]
    ).build(tasks_latest=1)
    assert "NOTE_4" in digest
    assert "### T-004" in digest
    for dropped in ("NOTE_1", "NOTE_2", "NOTE_3", "### T-001"):
        assert dropped not in digest


def test_zero_tasks_latest_empties_the_summary_instead_of_passing_all_rows():
    digest = _service(tasks=[_task(id="T-001", notes="NOTE_1")]).build(tasks_latest=0)
    assert "## tasks (latest 0 of 1 records, newest last, summary:" in digest
    assert "T-001 |" not in digest
    assert "NOTE_1" not in digest


def test_capped_tables_keep_full_text_when_the_knobs_are_unset():
    """ノブ未指定の既定は蓋なし＝現行挙動（新オプションは既定出力を動かさない）。"""
    long_text = "あ" * 300
    digest = _service(profile=[_profile(content=long_text)]).build()
    assert "## profile (1 records, full)" in digest
    assert _table_json(digest, "profile")[0]["content"] == long_text


def test_stage2_knobs_unset_keep_the_default_snapshot():
    """4 ノブを明示的に None で渡しても既定と 1 バイト違わない（後方互換の第四の錠）。"""
    assert (
        _snapshot_digest(
            profile_cap=None,
            individuals_cap=None,
            abilities_cap=None,
            tasks_latest=None,
        )
        == _DEFAULT_DIGEST_SNAPSHOT
    )


# === 主題軸: 索引併記と subject 絞り（category と直交する引き出し口、v1.9.0 Stage 3） ===

from usecases.orientation import filter_knowledge_by_subject  # noqa: E402


def _subjected_knowledge() -> list[dict]:
    """category（認識の型）と subjects（主題）が直交している状態の見本。

    K-004 は subjects を持たない既存レコード（201 件の初期状態）を模す。
    """
    return [
        _knowledge(id="K-001", topic="馬房の掃除", category="ops", subjects=["馬"]),
        _knowledge(
            id="K-002", topic="請求の締め", category="billing", subjects=["経営"]
        ),
        _knowledge(
            id="K-003", topic="厩舎の見積", category="billing", subjects=["馬", "建設"]
        ),
        _knowledge(id="K-004", topic="鍵の預かり", category="ops"),
        _knowledge(
            id="K-005", topic="馬の教え方", category="ops", subjects=["馬", "方法論"]
        ),
    ]


def test_index_knowledge_lists_subjects_between_the_id_and_the_topic():
    """索引は `id | subjects | topic`——主題は `/` 連結で 1 列に併記する。"""
    line = index_knowledge(
        _knowledge(id="K-001", topic="馬房の掃除", subjects=["馬", "方法論"])
    )
    assert line == "K-001 | 馬/方法論 | 馬房の掃除"


def test_index_knowledge_renders_missing_subjects_as_placeholder():
    """subjects の無いレコードは `-`——列が消えると読み手が桁をずらして誤読する。

    `summarize_task` の due_date と同じ理由。既存 201 件は subjects 未設定で始まるため、
    移行期間中は大半がこの形で並ぶ。
    """
    assert index_knowledge(_knowledge(id="K-001", topic="鍵の預かり")) == (
        "K-001 | - | 鍵の預かり"
    )
    assert index_knowledge(_knowledge(id="K-001", topic="鍵の預かり", subjects=[])) == (
        "K-001 | - | 鍵の預かり"
    )


def test_subjects_column_does_not_eat_into_the_topic_width():
    """併記列は topic_width の外側——主題を足しただけで topic の丸め幅が縮んではならない。"""
    bare = index_knowledge(_knowledge(topic="あ" * 300), topic_width=40)
    with_subjects = index_knowledge(
        _knowledge(topic="あ" * 300, subjects=["馬", "建設"]), topic_width=40
    )
    assert bare.split(" | ")[2] == with_subjects.split(" | ")[2]
    assert _utf8_len(with_subjects.split(" | ")[2]) <= 40


def test_filter_knowledge_by_subject_matches_a_single_element_exactly():
    """完全一致で 1 要素を引く（前方一致にしない——`filter_knowledge_by_category` と同型）。"""
    rows = _subjected_knowledge()
    assert [r["id"] for r in filter_knowledge_by_subject(rows, "建設")] == ["K-003"]
    assert filter_knowledge_by_subject(rows, "建") == []


def test_knowledge_subject_filters_rows_and_reports_hidden_count():
    """subjects に該当する行だけを出し、見出しの `N of M` と `subject=X` で絞りを開示する。"""
    digest = _service(knowledge=_subjected_knowledge()).build(knowledge_subject="馬")
    assert (
        "## knowledge (3 of 5 records, subject=馬, index: id | subjects | topic)"
        in digest
    )
    for shown in ("K-001 |", "K-003 |", "K-005 |"):
        assert shown in digest
    for hidden in ("K-002 |", "K-004 |"):
        assert hidden not in digest


def test_unknown_knowledge_subject_yields_zero_rows_without_error():
    """語彙外の subject は 0 行＋見出しのみ。絞りは観測であって検証ではない（照合は add 側の仕事）。"""
    digest = _service(knowledge=_subjected_knowledge()).build(knowledge_subject="宇宙")
    assert (
        "## knowledge (0 of 5 records, subject=宇宙, index: id | subjects | topic)"
        in digest
    )
    assert "K-00" not in digest


def test_knowledge_subject_applies_after_the_category_filter():
    """category → subject の順（母数 M は両方を掛けた後の件数、開示は元の全件との比）。"""
    digest = _service(knowledge=_subjected_knowledge()).build(
        knowledge_category="ops", knowledge_subject="馬"
    )
    assert (
        "## knowledge (2 of 5 records, category=ops, subject=馬, "
        "index: id | subjects | topic)" in digest
    )
    assert "K-001 |" in digest and "K-005 |" in digest
    assert "K-003 |" not in digest  # 馬だが billing


def test_knowledge_latest_applies_after_both_filters():
    """絞り順序は category → subject → latest に固定する。

    latest を先に効かせると「新しい N 件に該当が無ければ 0 件」になり、絞りの意味が壊れる
    ——この見本では latest 先行なら K-005 の 1 件しか残らない（K-001 が落ちる）。
    """
    digest = _service(knowledge=_subjected_knowledge()).build(
        knowledge_category="ops", knowledge_subject="馬", knowledge_latest=2
    )
    assert (
        "## knowledge (latest 2 of 2 records, newest last, category=ops, subject=馬, "
        "index: id | subjects | topic)" in digest
    )
    assert "K-001 |" in digest and "K-005 |" in digest


def test_knowledge_subject_does_not_affect_other_sections():
    """絞りは knowledge セクション限定（counts は表の実件数のまま＝母数を隠さない）。"""
    digest = _service(knowledge=_subjected_knowledge(), tasks=[_task()]).build(
        knowledge_subject="馬"
    )
    assert "knowledge: 5 records, 0 bytes" in digest
    assert "T-001 |" in digest


def test_knowledge_subject_unset_keeps_the_default_snapshot():
    """`knowledge_subject` を明示的に None で渡しても既定と同一（後方互換の第五の錠）。"""
    assert _snapshot_digest(knowledge_subject=None) == _DEFAULT_DIGEST_SNAPSHOT


# === 三表の処方: subjects / steps の索引化と goals の cap（v1.10.0 Stage 1） ===

# subjects / steps の描画は本サイクルで**意図的に**変える（v1.9.0 の索引 3 列化と同じ扱い）。
# 変えない側を先に機械で固定するのがこのブロックの錠——**v1.9.0 の出力から転記した
# 6 表分の literal** で、以後の描画変更がここへ滲み出したら即座に割れる。
_UNRELATED_SECTIONS = (
    "individuals",
    "tasks",
    "tasks.notes",
    "knowledge",
    "abilities",
    "profile",
    "goals",
)

_UNRELATED_SECTIONS_SNAPSHOT = """## individuals (1 records, full)
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

## knowledge (2 records, index: id | subjects | topic)
K-001 | - | 申し送りの置き場
K-002 | - | 請求の締め

## abilities (0 records, full)
[]

## profile (0 records, full)
[]

## goals (0 records, full)
[]
"""


def _section(digest: str, name: str) -> str:
    """`## name (` の見出し行から次の見出し直前までを、見出し込みで切り出す。"""
    body = digest.split(f"\n## {name} (", 1)[1]
    return f"## {name} (" + body.split("\n## ", 1)[0]


def test_unrelated_sections_keep_the_default_snapshot():
    """subjects / steps の描画を変えても、他 6 表の既定出力は 1 バイトも動かない。

    契約面（秘書が毎枠読む digest）の変更を「意図した 2 セクション」に閉じ込める錠。
    tasks は要約と `tasks.notes` の 2 ブロックを持つので両方を突き合わせる。
    """
    digest = _snapshot_digest()
    rendered = "\n".join(_section(digest, name) for name in _UNRELATED_SECTIONS)
    assert rendered == _UNRELATED_SECTIONS_SNAPSHOT


def _subject(**kw) -> dict:
    base = {
        "id": "馬",
        "label": "馬",
        "aliases": [],
        "status": "active",
        "note": "",
        "created_at": "t",
        "updated_at": "t",
    }
    base.update(kw)
    return base


def _step(**kw) -> dict:
    base = {
        "id": "S-001",
        "goal_id": "G-001",
        "title": "見積を集める",
        "seq": 1,
        "status": "todo",
        "due_date": None,
        "notes": "",
        "created_at": "t",
        "updated_at": "t",
    }
    base.update(kw)
    return base


def _goal(**kw) -> dict:
    base = {
        "id": "G-001",
        "title": "厩舎を建てる",
        "category": "work",
        "status": "active",
        "target_date": None,
        "success_criteria": "",
        "notes": "",
        "created_at": "t",
        "updated_at": "t",
        "closed_at": None,
    }
    base.update(kw)
    return base


def test_subjects_index_keeps_the_vocabulary_selectable():
    """語彙は全量載り（id / label / aliases / status）、幅で丸まるのは note だけ。

    subjects は `--knowledge-subject` に渡す語を選ぶための一覧なので、選択に要る 4 列は
    索引でも欠かさない。cap でなく索引を採るのは `subjects add` で件数が増える表だから
    ——cap は 1 レコードの長さにしか効かない（DESIGN の表の性質→処方）。
    """
    digest = _service(
        subjects=[
            _subject(id="馬", aliases=["horse", "馬事"], note="の" * 300),
            _subject(id="建設", label="建設", status="deprecated"),
        ]
    ).build()
    assert (
        "## subjects (2 records, index: id | label | aliases | status | note)" in digest
    )
    assert "建設 | 建設 | - | deprecated | " in digest  # aliases 空は `-`
    horse = next(ln for ln in digest.splitlines() if ln.startswith("馬 | "))
    note = horse.split(" | ")[4]
    assert _utf8_len(note) <= DEFAULT_TOPIC_WIDTH  # 幅は knowledge の topic 列に揃える
    assert note.endswith(TRUNCATION_MARK)
    assert "created_at" not in digest  # 索引は timestamps を運ばない（行あたり最小）


def test_subjects_are_sorted_by_id_ascending():
    digest = _service(
        subjects=[_subject(id="S-003"), _subject(id="S-001"), _subject(id="S-002")]
    ).build()
    assert digest.index("S-001 |") < digest.index("S-002 |") < digest.index("S-003 |")


def test_steps_index_drops_the_notes_and_keeps_the_ordering_columns():
    """索引は `id | goal_id | seq | status | title`——notes は載せない（読み筋は `get --key`）。"""
    digest = _service(steps=[_step(notes="STEP_NOTES_MARKER")]).build()
    assert "## steps (1 records, index: id | goal_id | seq | status | title)" in digest
    assert "S-001 | G-001 | 1 | todo | 見積を集める" in digest
    assert "STEP_NOTES_MARKER" not in digest


def test_steps_latest_keeps_the_newest_and_discloses_the_total():
    """一行索引を id 昇順の末尾 N 件に絞り、見出しの `latest N of M` で母数を開示する。

    steps は設計上 `done` が高速に溜まる（目標からの逆算単位）——選び方も開示も
    `_tasks_section` と同型で、新しい並べ替えは持ち込まない（`pick_latest_by_id` の再利用）。
    """
    digest = _service(steps=[_step(id=f"S-00{i}", seq=i) for i in range(1, 5)]).build(
        steps_latest=2
    )
    assert (
        "## steps (latest 2 of 4 records, newest last, "
        "index: id | goal_id | seq | status | title)" in digest
    )
    assert digest.index("S-003 |") < digest.index("S-004 |")
    for dropped in ("S-001 |", "S-002 |"):
        assert dropped not in digest


def test_goals_cap_bounds_the_notes_and_discloses_the_cap():
    """goals の支配項 notes に蓋を掛け、掛けた事実を見出しで開示する（profile と同型）。

    goals は件数が少なく本文が長い側なので処方は cap——`_CAP_FIELDS` へ 1 行足すだけで
    丸め規約・非破壊複製・開示が付く。
    """
    record = _goal(notes="あ" * 500, success_criteria="上棟する")
    digest = _service(goals=[record]).build(goals_cap=100)
    assert "## goals (1 records, full, notes cap 100 bytes)" in digest
    capped = _table_json(digest, "goals")[0]
    assert _utf8_len(capped["notes"]) <= 100
    assert capped["notes"].endswith(TRUNCATION_MARK)
    assert capped["success_criteria"] == "上棟する"  # 丸めるのは支配項 1 つだけ
    assert record["notes"] == "あ" * 500  # 入力レコードは汚さない


def test_stage1_knobs_unset_keep_the_default_snapshot():
    """新ノブ 2 種を明示的に None で渡しても既定と 1 バイト違わない（後方互換の第六の錠）。"""
    assert (
        _snapshot_digest(goals_cap=None, steps_latest=None) == _DEFAULT_DIGEST_SNAPSHOT
    )
