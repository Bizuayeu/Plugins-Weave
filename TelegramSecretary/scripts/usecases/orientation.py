"""起動時オリエンテーションのダイジェスト射影（UseCase、I/O を知らない）。

全表を並べた一括 list（当時 7 表で 1.6MB 規模）はハーネスの出力上限を超えて persisted-output へ退避し、
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

# 既定値の出所: notes_tail / topic_width / handoff 系はいずれも orientation_report_20260809
# （notes_tail は申し送りが notes 末尾 3,000–4,000 字に堆積する運用実測、topic_width は同レポート
# 指定、handoff_cap は 1 枠の申し送り実測からの外挿で**仮置き**——CLI オプションで上書きし、
# 次枠の実測で校正する）。単位は **UTF-8 バイト**（v1.7.0）——v1.5.0 校正値の実効意図
# （1 字 1 バイト世界での 120B / 4000B）を orientation_datafit_20260809 実測（日本語
# 1 字≈2.47B）に基づき単位是正した。数値は不変で、出力上限（バイト）と同じ単位になる。
DEFAULT_NOTES_TAIL = 4000
DEFAULT_TOPIC_WIDTH = 120
DEFAULT_HANDOFF_LATEST = 3  # 件数（単位是正の外）
DEFAULT_HANDOFF_CAP = 8000

# 切り取りが起きたことを読み手（秘書）に示すマーカー（UTF-8 で 3 バイト＝幅の一部を占める）
TRUNCATION_MARK = "…"
_MARK_BYTES = len(TRUNCATION_MARK.encode("utf-8"))

# 一行要約に載せる tasks の status（done は要約行のみで notes を載せない）
ACTIVE_TASK_STATUSES = frozenset({"open", "in_progress", "blocked"})

# 全文で載る小表の「支配的長文フィールド」への経路（orientation_report_20260810 実測の支配項）。
# 蓋はここだけに掛ける——レコード全体の JSON を丸めると構造が壊れ、個票を `get --key` で
# 引き直す読み筋まで死ぬ。goals は件数が少なく本文が長い側なのでここに載る。件数が増える側
# （subjects / steps）は cap では有界にならないので索引で処方する（表の性質が処方を決める）
_CAP_FIELDS: Mapping[str, tuple[str, ...]] = {
    "individuals": ("identity", "context_notes"),
    "abilities": ("guidance",),
    "profile": ("content",),
    "goals": ("notes",),
}


class RecordLister(Protocol):
    """`RegistryService.list()` の読み取り面だけを要求する（差し替え可能性の確保）。"""

    def list(self) -> list[dict[str, Any]]: ...


def _utf8_len(text: str) -> int:
    return len(text.encode("utf-8"))


def _head_bytes(text: str, budget: int) -> str:
    """先頭から budget バイトに収まる分だけ返す（文字ごとに積算し、境界で止める）。"""
    kept: list[str] = []
    used = 0
    for char in text:
        size = _utf8_len(char)
        if used + size > budget:
            break
        kept.append(char)
        used += size
    return "".join(kept)


def _tail_bytes(text: str, budget: int) -> str:
    """末尾から budget バイトに収まる分だけ返す（`_head_bytes` の逆走）。"""
    kept: list[str] = []
    used = 0
    for char in reversed(text):
        size = _utf8_len(char)
        if used + size > budget:
            break
        kept.append(char)
        used += size
    return "".join(reversed(kept))


def _truncate(text: str, width: int) -> str:
    """width バイト（UTF-8）以内に収める（切ったら末尾にマーカー）。

    幅をバイトで数えるのは、出力上限（persisted-output 退避の閾値）がバイトだから——
    字数で数えると日本語 1 字≈2.47 バイトの分だけ実効幅が膨らむ。丸めは文字境界で止め、
    マーカー（3 バイト）は幅の内側に置く。width が非正なら全捨て（マーカーのみ）。ここで
    元テキストを返すと、絞るためのオプションが逆に全文を通す穴になる——有界性はこの関数の
    責務なので閉じる。
    """
    if width <= 0:
        return TRUNCATION_MARK
    if _utf8_len(text) <= width:
        return text
    return _head_bytes(text, width - _MARK_BYTES) + TRUNCATION_MARK


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
    """knowledge の索引行 `id | subjects | topic`。content は**載せない**（943KB の支配項）。

    主題は `/` 連結の 1 列に併記し、未設定は `-`（列が消えると読み手が桁をずらして誤読する
    ——`summarize_task` の due_date と同じ理由）。併記列は topic_width の**外側**に置く
    ——主題を足したせいで topic の丸め幅が縮むと、索引の読める量が主題の付き方で揺れる。
    """
    subjects = "/".join(str(s) for s in record.get("subjects", []) or []) or "-"
    topic = _truncate(str(record.get("topic", "")), topic_width)
    return f"{record.get('id', '')} | {subjects} | {topic}"


def index_subject(
    record: Mapping[str, Any], note_width: int = DEFAULT_TOPIC_WIDTH
) -> str:
    """subjects の索引行 `id | label | aliases | status | note`。timestamps は**載せない**。

    語彙は `subjects add` で育つ＝件数が増える表なので、処方は cap ではなく索引にする
    （cap は 1 レコードの長さにしか効かない）。この表は `--knowledge-subject` に渡す語を
    選ぶための一覧なので、選択に要る 4 列は全量載せ、丸めるのは note だけ。aliases は
    `/` 連結の 1 列・空は `-`（列が消えると読み手が桁をずらして誤読する——`index_knowledge`
    の subjects 列と同じ流儀）。
    """
    aliases = "/".join(str(a) for a in record.get("aliases", []) or []) or "-"
    note = _truncate(str(record.get("note", "")), note_width)
    return " | ".join(
        [
            str(record.get("id", "")),
            str(record.get("label", "")),
            aliases,
            str(record.get("status", "")),
            note,
        ]
    )


def index_step(record: Mapping[str, Any]) -> str:
    """steps の索引行 `id | goal_id | seq | status | title`。notes は**載せない**。

    目標からの逆算単位ゆえ設計上 `done` が高速に溜まる＝件数が増える表で、処方は tasks と
    同じ「一行＋件数絞り」。落ちた行と notes の読み筋は `get --key`（`summarize_task` と同型）。
    """
    return " | ".join(
        [
            str(record.get("id", "")),
            str(record.get("goal_id", "")),
            str(record.get("seq", "")),
            str(record.get("status", "")),
            str(record.get("title", "")),
        ]
    )


def cap_record_field(
    record: Mapping[str, Any], path: Sequence[str], cap: int
) -> dict[str, Any]:
    """レコードの支配的長文フィールド 1 つだけを cap バイトで丸めた複製を返す。

    丸め方は `_truncate` に委ねる（バイト・文字境界・マーカーは幅の内側・非正は全捨て）——
    表ごとに丸め規約が分岐すると、読み手が「どこで切れたか」を表ごとに覚える羽目になる。
    経路上のキーが無いレコードは素通し（表の形はデータ側の都合で欠けうる）。入力は変更せず、
    経路上の dict だけを複製する——lister が返した実体を汚すと後段の counts / role が
    丸め後の値を読む。
    """
    copied = dict(record)
    cursor = copied
    for key in path[:-1]:
        nested = cursor.get(key)
        if not isinstance(nested, dict):
            return copied
        cursor[key] = dict(nested)
        cursor = cursor[key]
    leaf = path[-1]
    if leaf in cursor:
        cursor[leaf] = _truncate(str(cursor[leaf]), cap)
    return copied


def filter_knowledge_by_category(
    rows: Sequence[Mapping[str, Any]], category: str
) -> list[dict[str, Any]]:
    """knowledge を category **完全一致**で絞る（前方一致にしない——絞りの意味が曖昧になる）。

    索引は O(n) で全件並ぶため、表が育つほど起動時の読み負荷が効いてくる。絞りは母数側から
    それを抑える観測手段であり、検証ではない（該当 0 件はエラーではなく「その category の
    知見はまだ無い」という観測結果）。隠れた件数は呼び出し側が見出しの `of M` で開示する。
    """
    return [dict(row) for row in rows if str(row.get("category", "")) == category]


def filter_knowledge_by_subject(
    rows: Sequence[Mapping[str, Any]], subject: str
) -> list[dict[str, Any]]:
    """knowledge を subjects の**要素の完全一致**で絞る（`filter_knowledge_by_category` の同型）。

    category（認識の型・閉じた語彙）と直交する主題の引き出し口。ここも検証ではなく観測——
    語彙外の subject は 0 件という観測結果であってエラーではない（語彙の照合は add / import
    の書き込み口が SUBJECTS テーブルを引いて行う）。subjects を持たないレコードは該当しない。
    """
    return [
        dict(row)
        for row in rows
        if subject in [str(s) for s in row.get("subjects", []) or []]
    ]


def pick_latest_by_id(
    rows: Sequence[Mapping[str, Any]], latest: int
) -> list[dict[str, Any]]:
    """レコード群を id 昇順の**末尾** latest 件＝新しい順 N 件に絞る（knowledge / tasks 共用）。

    id は日付順に振られるため id の大きい方が新しい——「新しい順に選ぶ」は
    `pick_latest_handoffs`（名前降順）と同じ読み筋。並べ替えては返さない（索引の読み方は
    変えず、母数だけを減らす観測手段＝`filter_knowledge_by_category` と同格）。非正の
    latest は 0 件——`rows[-0:]` が全件に化ける罠を塞ぐ（`tail_notes` と同じ理由）。
    """
    if latest <= 0:
        return []
    ordered = sorted(rows, key=lambda r: str(r.get("id", "")))
    return [dict(row) for row in ordered[-latest:]]


def tail_notes(notes: str, notes_tail: int = DEFAULT_NOTES_TAIL) -> str:
    """notes の末尾 notes_tail バイト（申し送りは末尾に堆積するため頭を捨てる）。

    数え方と丸め位置は `_truncate` と同じ（UTF-8 バイト・文字境界・マーカーは幅の内側）。
    非正の notes_tail は全捨て（`notes[-0:]` が全文になる罠を塞ぐ、_truncate と同じ理由）。
    """
    if notes_tail <= 0:
        return TRUNCATION_MARK
    if _utf8_len(notes) <= notes_tail:
        return notes
    return TRUNCATION_MARK + _tail_bytes(notes, notes_tail - _MARK_BYTES)


def pick_latest_handoffs(
    blocks: Sequence[tuple[str, str]],
    latest: int = DEFAULT_HANDOFF_LATEST,
    cap: int = DEFAULT_HANDOFF_CAP,
) -> list[tuple[str, str]]:
    """(ファイル名, 本文) 群から名前**降順**に latest 件選び、各本文を cap バイトで丸める。

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
        knowledge_subject: str | None = None,
        knowledge_latest: int | None = None,
        individuals_cap: int | None = None,
        abilities_cap: int | None = None,
        profile_cap: int | None = None,
        goals_cap: int | None = None,
        tasks_latest: int | None = None,
        steps_latest: int | None = None,
    ) -> str:
        # None は「蓋なし＝現行挙動」。0 は「マーカーのみ／0 件」という指定なので
        # falsy では分岐しない（判定は is not None）
        caps = {
            "individuals": individuals_cap,
            "abilities": abilities_cap,
            "profile": profile_cap,
            "goals": goals_cap,
        }
        records = {name: lister.list() for name, lister in self._listers.items()}
        parts = ["# orientation", ""]
        parts += self._role_section(records)
        parts += self._counts_section(records)
        for name in records:
            parts += self._table_section(
                name,
                records[name],
                notes_tail,
                topic_width,
                knowledge_category,
                knowledge_subject,
                knowledge_latest,
                caps,
                tasks_latest,
                steps_latest,
            )
        parts += self._handoff_section(handoffs, handoff_latest, handoff_cap)
        return "\n".join(parts)

    # --- sections ---

    def _role_section(self, records: Mapping[str, list[dict[str, Any]]]) -> list[str]:
        """役割はコードが決める（derive_role、DESIGN §3.11）——role-status と同一の判定。"""
        status = derive_role(records.get("profile", []), records.get("goals", []))
        return [
            "## role",
            json.dumps(status.to_dict(), ensure_ascii=False),
            "",
        ]

    def _counts_section(self, records: Mapping[str, list[dict[str, Any]]]) -> list[str]:
        lines = ["## counts"]
        lines += [
            f"{name}: {len(rows)} records, {self._sizes.get(name, 0)} bytes"
            for name, rows in records.items()
        ]
        return [*lines, ""]

    def _table_section(
        self,
        name: str,
        rows: list[dict[str, Any]],
        notes_tail: int,
        topic_width: int,
        knowledge_category: str | None,
        knowledge_subject: str | None,
        knowledge_latest: int | None,
        caps: Mapping[str, int | None],
        tasks_latest: int | None,
        steps_latest: int | None,
    ) -> list[str]:
        if name == "tasks":
            return self._tasks_section(rows, notes_tail, tasks_latest)
        if name == "knowledge":
            return self._knowledge_section(
                rows,
                topic_width,
                knowledge_category,
                knowledge_subject,
                knowledge_latest,
            )
        if name == "subjects":
            return self._subjects_section(rows)
        if name == "steps":
            return self._steps_section(rows, steps_latest)
        # 既定は全文（小表＝individuals / abilities / profile / goals。いずれも件数が少なく
        # 1 レコードが長い側なので、蓋は _CAP_FIELDS の cap で掛ける）。
        # 表が増えても列挙漏れで欠落しない側に倒す（肥大したらここで射影を足す）
        cap = caps.get(name)
        path = _CAP_FIELDS.get(name)
        scope = ""
        if cap is not None and path is not None:
            rows = [cap_record_field(row, path, cap) for row in rows]
            # 蓋の存在と適用先を見出しで開示する（丸めた事実を読み手に隠さない＝`N of M` と同趣旨）
            scope = f", {'.'.join(path)} cap {cap} bytes"
        return [
            f"## {name} ({len(rows)} records, full{scope})",
            json.dumps(rows, ensure_ascii=False, indent=2),
            "",
        ]

    def _tasks_section(
        self, rows: list[dict[str, Any]], notes_tail: int, latest: int | None = None
    ) -> list[str]:
        """一行要約を latest で絞り、notes は**絞った集合に連動**させる。

        落ちた task の notes だけが残ると、要約に無い id の申し送りを読む羽目になる
        （落ちた分の読み筋は `get --key`）。母数は見出しの `of M` で開示する。
        """
        ordered = sorted(rows, key=lambda r: str(r.get("id", "")))
        total = len(ordered)
        if latest is None:
            count = f"{total} records"
        else:
            ordered = pick_latest_by_id(ordered, latest)
            count = f"latest {len(ordered)} of {total} records, newest last"
        lines = [
            f"## tasks ({count}, summary: id | status | priority | due_date | title)"
        ]
        lines += [summarize_task(t) for t in ordered]
        lines += ["", f"## tasks.notes (active only, last {notes_tail} bytes)"]
        for task in ordered:
            if task.get("status") not in ACTIVE_TASK_STATUSES:
                continue  # done の notes は載せない（過去の申し送りは digest の対象外）
            notes = str(task.get("notes", ""))
            if not notes:
                continue
            lines += [f"### {task.get('id', '')}", tail_notes(notes, notes_tail)]
        return [*lines, ""]

    def _knowledge_section(
        self,
        rows: list[dict[str, Any]],
        topic_width: int,
        category: str | None = None,
        subject: str | None = None,
        latest: int | None = None,
    ) -> list[str]:
        """索引を category → subject → latest の順で絞る（latest の母数 M は絞り後の件数）。

        latest が先だと「新しい N 件に該当 category / subject が無ければ 0 件」になり、
        絞りの意味が壊れる。category（認識の型）と subject（主題）は直交する軸なので
        順序は結果を変えないが、母数 M の意味を「両方を掛けた後の件数」に固定するため
        並びを決めておく。どの絞りも見出しに `of M` を残す——見えなくなった件数は開示する。
        """
        ordered = sorted(rows, key=lambda r: str(r.get("id", "")))
        if category is not None:
            ordered = filter_knowledge_by_category(ordered, category)
        if subject is not None:
            ordered = filter_knowledge_by_subject(ordered, subject)
        total = len(ordered)
        narrowed = category is not None or subject is not None
        if latest is None:
            count = (
                f"{total} of {len(rows)} records" if narrowed else f"{total} records"
            )
        else:
            ordered = pick_latest_by_id(ordered, latest)
            # 選ぶのは新しい順・並びは id 昇順という捻れを、読み方の開示で解く（末尾が最新）
            count = f"latest {len(ordered)} of {total} records, newest last"
        scope = "" if category is None else f", category={category}"
        scope += "" if subject is None else f", subject={subject}"
        lines = [
            f"## knowledge ({count}{scope}, index: id | subjects | topic)",
            *[index_knowledge(k, topic_width) for k in ordered],
        ]
        return [*lines, ""]

    def _subjects_section(self, rows: list[dict[str, Any]]) -> list[str]:
        """語彙を id 昇順の索引で**全量**並べる（件数絞りは付けない）。

        この表は「どの主題で knowledge を引くか」を選ぶための一覧なので、母数を減らすと
        選べない語が出る——絞るべきは索引の**行あたりの重さ**であって件数ではない。
        """
        ordered = sorted(rows, key=lambda r: str(r.get("id", "")))
        lines = [
            f"## subjects ({len(ordered)} records, "
            "index: id | label | aliases | status | note)",
            *[index_subject(s) for s in ordered],
        ]
        return [*lines, ""]

    def _steps_section(
        self, rows: list[dict[str, Any]], latest: int | None = None
    ) -> list[str]:
        """索引を latest で絞る（`_tasks_section` と同型、母数は見出しの `of M` で開示）。

        選ぶのは新しい順・並びは id 昇順という捻れの解き方も tasks / knowledge と同じ
        （`newest last` は絞ったときだけ載せる——全件に付けると並び順の誤読を生む）。
        """
        ordered = sorted(rows, key=lambda r: str(r.get("id", "")))
        total = len(ordered)
        if latest is None:
            count = f"{total} records"
        else:
            ordered = pick_latest_by_id(ordered, latest)
            count = f"latest {len(ordered)} of {total} records, newest last"
        lines = [
            f"## steps ({count}, index: id | goal_id | seq | status | title)",
            *[index_step(s) for s in ordered],
        ]
        return [*lines, ""]

    def _handoff_section(
        self, handoffs: Sequence[tuple[str, str]], latest: int, cap: int
    ) -> list[str]:
        picked = pick_latest_handoffs(handoffs, latest, cap)
        lines = [f"## handoff ({len(picked)} blocks, latest {latest}, cap {cap} bytes)"]
        for name, body in picked:
            lines += [f"### {name}", body]
        return [*lines, ""]
