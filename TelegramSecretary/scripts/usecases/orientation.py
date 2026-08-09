"""起動時オリエンテーションのダイジェスト射影（UseCase、I/O を知らない）。

7表の一括 list（1.6MB 規模）はハーネスの出力上限を超えて persisted-output へ退避し、
**データがコンテキストに載らないまま exit 0 する沈黙失敗**を起こしていた。本モジュールは
その代わりに読ませる「絞り込みダイジェスト」を組む——出力量が入力（notes / content）の
長さに依存せず、`notes_tail × active 件数 + 索引行数` に**有界**であることが要件。

射影は純関数（`summarize_task` / `index_knowledge` / `tail_notes` / `pick_latest_handoffs`）
に切り出し、`OrientationService` は注入された lister（`.list()` を持つ）と
ファイルサイズを組み立てるだけ。ファイル読み・サイズ取得・表の並び順は CLI（Interface）が注入する
——表の並びは REGISTRY_SPEC（SSoT）のキー順がそのまま渡るので、表追加に自動追従する。
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from domain.registry import derive_role

# 既定値の出所: notes_tail / topic_width / handoff 系はいずれも orientation_report_20260809。
# notes_tail=4000 は申し送りが notes 末尾 3,000–4,000 字に堆積する運用実測、topic_width=120 は
# 同レポート指定。handoff_latest=3 / handoff_cap=8000 は実測（1 枠の申し送り数千字）からの
# 外挿で**仮置き**——CLI オプションで上書きし、次枠の実測で校正する。
DEFAULT_NOTES_TAIL = 4000
DEFAULT_TOPIC_WIDTH = 120
DEFAULT_HANDOFF_LATEST = 3
DEFAULT_HANDOFF_CAP = 8000

# 切り取りが起きたことを読み手（秘書）に示す 1 字マーカー
TRUNCATION_MARK = "…"

# 一行要約に載せる tasks の status（done は要約行のみで notes を載せない）
ACTIVE_TASK_STATUSES = frozenset({"open", "in_progress", "blocked"})


class RecordLister(Protocol):
    """`RegistryService.list()` の読み取り面だけを要求する（差し替え可能性の確保）。"""

    def list(self) -> list[dict]: ...


def _truncate(text: str, width: int) -> str:
    """width 字以内に収める（切ったら末尾にマーカー、返り値は width 字を超えない）。

    width が非正なら全捨て（マーカーのみ）。ここで元テキストを返すと、絞るための
    オプションが逆に全文を通す穴になる——有界性はこの関数の責務なので閉じる。
    """
    if width <= 0:
        return TRUNCATION_MARK
    if len(text) <= width:
        return text
    return text[: width - 1] + TRUNCATION_MARK


def summarize_task(task: Mapping[str, Any]) -> str:
    """tasks の一行要約 `id | status | priority | due_date | title`。

    未設定の due_date は `-`（列が消えると読み手が桁をずらして誤読する）。
    """
    return " | ".join(
        [
            str(task.get("id", "")),
            str(task.get("status", "")),
            str(task.get("priority", "")),
            str(task.get("due_date") or "-"),
            str(task.get("title", "")),
        ]
    )


def index_knowledge(
    record: Mapping[str, Any], topic_width: int = DEFAULT_TOPIC_WIDTH
) -> str:
    """knowledge の索引行 `id | topic`。content は**載せない**（943KB の支配項）。"""
    return f"{record.get('id', '')} | {_truncate(str(record.get('topic', '')), topic_width)}"


def filter_knowledge_by_category(
    rows: Sequence[Mapping[str, Any]], category: str
) -> list[dict]:
    """knowledge を category **完全一致**で絞る（前方一致にしない——絞りの意味が曖昧になる）。

    索引は O(n) で全件並ぶため、表が育つほど起動時の読み負荷が効いてくる。絞りは母数側から
    それを抑える観測手段であり、検証ではない（該当 0 件はエラーではなく「その categoryの
    知見はまだ無い」という観測結果）。隠れた件数は呼び出し側が見出しの `of M` で開示する。
    """
    return [dict(row) for row in rows if str(row.get("category", "")) == category]


def tail_notes(notes: str, notes_tail: int = DEFAULT_NOTES_TAIL) -> str:
    """notes の末尾 notes_tail 字（申し送りは末尾に堆積するため頭を捨てる）。

    非正の notes_tail は全捨て（`notes[-0:]` が全文になる罠を塞ぐ、_truncate と同じ理由）。
    """
    if notes_tail <= 0:
        return TRUNCATION_MARK
    if len(notes) <= notes_tail:
        return notes
    return TRUNCATION_MARK + notes[-notes_tail:]


def pick_latest_handoffs(
    blocks: Sequence[tuple[str, str]],
    latest: int = DEFAULT_HANDOFF_LATEST,
    cap: int = DEFAULT_HANDOFF_CAP,
) -> list[tuple[str, str]]:
    """(ファイル名, 本文) 群から名前**降順**に latest 件選び、各本文を cap 字で丸める。

    中身は解釈しない（DESIGN §3.10 スキーマレス原則）——標準化するのは
    「置き場と命名の辞書順ソート可能性」だけ。命名が UTC 日時始まりゆえ名前降順＝新しい順。
    """
    picked = sorted(blocks, key=lambda b: b[0], reverse=True)[: max(latest, 0)]
    return [(name, _truncate(body, cap)) for name, body in picked]


class OrientationService:
    """注入された表（lister）とファイルサイズからオリエンテーション digest を組む。"""

    def __init__(
        self, listers: Mapping[str, RecordLister], sizes: Mapping[str, int]
    ) -> None:
        self._listers = listers
        self._sizes = sizes

    def build(
        self,
        *,
        handoffs: Sequence[tuple[str, str]] = (),
        notes_tail: int = DEFAULT_NOTES_TAIL,
        topic_width: int = DEFAULT_TOPIC_WIDTH,
        handoff_latest: int = DEFAULT_HANDOFF_LATEST,
        handoff_cap: int = DEFAULT_HANDOFF_CAP,
        knowledge_category: str | None = None,
    ) -> str:
        records = {name: lister.list() for name, lister in self._listers.items()}
        parts = ["# orientation", ""]
        parts += self._role_section(records)
        parts += self._counts_section(records)
        for name in records:
            parts += self._table_section(
                name, records[name], notes_tail, topic_width, knowledge_category
            )
        parts += self._handoff_section(handoffs, handoff_latest, handoff_cap)
        return "\n".join(parts)

    # --- sections ---

    def _role_section(self, records: Mapping[str, list[dict]]) -> list[str]:
        """役割はコードが決める（derive_role、DESIGN §3.11）——role-status と同一の判定。"""
        status = derive_role(records.get("profile", []), records.get("goals", []))
        return [
            "## role",
            json.dumps(status.to_dict(), ensure_ascii=False),
            "",
        ]

    def _counts_section(self, records: Mapping[str, list[dict]]) -> list[str]:
        lines = ["## counts"]
        lines += [
            f"{name}: {len(rows)} records, {self._sizes.get(name, 0)} bytes"
            for name, rows in records.items()
        ]
        return [*lines, ""]

    def _table_section(
        self,
        name: str,
        rows: list[dict],
        notes_tail: int,
        topic_width: int,
        knowledge_category: str | None,
    ) -> list[str]:
        if name == "tasks":
            return self._tasks_section(rows, notes_tail)
        if name == "knowledge":
            return self._knowledge_section(rows, topic_width, knowledge_category)
        # 既定は全文（小表＝individuals / abilities / profile / goals / steps）。
        # 表が増えても列挙漏れで欠落しない側に倒す（肥大したらここで射影を足す）
        return [
            f"## {name} ({len(rows)} records, full)",
            json.dumps(rows, ensure_ascii=False, indent=2),
            "",
        ]

    def _tasks_section(self, rows: list[dict], notes_tail: int) -> list[str]:
        ordered = sorted(rows, key=lambda r: str(r.get("id", "")))
        lines = [
            f"## tasks ({len(ordered)} records, summary: id | status | priority | due_date | title)"
        ]
        lines += [summarize_task(t) for t in ordered]
        lines += ["", f"## tasks.notes (active only, last {notes_tail} chars)"]
        for task in ordered:
            if task.get("status") not in ACTIVE_TASK_STATUSES:
                continue  # done の notes は載せない（過去の申し送りは digest の対象外）
            notes = str(task.get("notes", ""))
            if not notes:
                continue
            lines += [f"### {task.get('id', '')}", tail_notes(notes, notes_tail)]
        return [*lines, ""]

    def _knowledge_section(
        self, rows: list[dict], topic_width: int, category: str | None = None
    ) -> list[str]:
        ordered = sorted(rows, key=lambda r: str(r.get("id", "")))
        if category is None:
            header = f"## knowledge ({len(ordered)} records, index: id | topic)"
        else:
            ordered = filter_knowledge_by_category(ordered, category)
            header = (
                f"## knowledge ({len(ordered)} of {len(rows)} records, "
                f"category={category}, index: id | topic)"
            )
        lines = [header, *[index_knowledge(k, topic_width) for k in ordered]]
        return [*lines, ""]

    def _handoff_section(
        self, handoffs: Sequence[tuple[str, str]], latest: int, cap: int
    ) -> list[str]:
        picked = pick_latest_handoffs(handoffs, latest, cap)
        lines = [f"## handoff ({len(picked)} blocks, latest {latest}, cap {cap} chars)"]
        for name, body in picked:
            lines += [f"### {name}", body]
        return [*lines, ""]
