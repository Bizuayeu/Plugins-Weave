"""納品物・handoff の裸数値スキャン（presence-only、数字の行に出所マーカーがあるかだけを見る）。

`output_scan.py` が送信本文の秘匿値を形状で検査するのに対し、こちらは原稿の数値に
**出所を名指す計器トークンが同じ行にあるか**だけを二値で返す。**presence の検査であって
正しさの検査ではない（計器あり ≠ その数が正しい）**——数値の妥当性は形状に現れないため、
読んで分類する責務はエージェント側に残る。

数字を含む行はすべて候補にする。ID・日付・セッション名も拾うが除外規則を持たない——
除外は妥当性判定の入口であり、presence-only の線を越えるため。ゆえに本モジュールの
役割は当たり付け（候補分析）どまりである。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 対象は納品物と handoff の原稿 md（presence-only）。機械は当たり付けどまりで、
# 裸箇所の名指しと正しさの確認はエージェント責務に残る（DESIGN §3.13）。

# 計器トークン（計器／導出元／継承の別を名指す語形）。SSoT は T0015 分析ノートの実践語彙で、
# linter はそれを部分文字列一致で近似する。`見積` `引き写` は語幹として置く（見積もり／
# 引き写した を拾うため）。一文字・高頻度語は入れない——偽陽性（covered を bare と呼ぶ）は
# 読み直し一回で安いが、偽陰性（偶然一致で bare が covered に化ける）は「緑を信じる」危険に
# 直結する。校正はこの定数 1 箇所の追補で行う。
GAUGE_TOKENS: tuple[str, ...] = (
    "実測",
    "実読",
    "直読",
    "走査",
    "照合",
    "申告",
    "導出",
    "計算",
    "概算",
    "推定",
    "見込み",
    "見積",
    "予告",
    "再構成",
    "仮置き",
    "引用",
    "出典",
    "継承",
    "引き写",
    "概数",
)

# 数字を含む行の検出。半角・全角の両方を 1 つの文字クラスで受ける（幅の扱いはこれで尽き、
# 追加の正規化は持たない——計器トークンは漢字・かなで幅の影響を受けない）。
_NUMBER_RE = re.compile(r"[0-9０-９]")


@dataclass(frozen=True)
class NumberLintReport:
    """行走査の集計。`number_lines == covered + bare` が常に成り立つ。"""

    number_lines: int
    covered: int
    bare: int
    bare_lines: list[tuple[int, str]]


def lint_numbers(text: str) -> NumberLintReport:
    """数字を含む各行について、同一行の計器トークン有無を二値で判定し集計を返す。

    `bare_lines` は (行番号, 行) の並びで、行番号は 1-indexed。
    """
    number_lines = 0
    covered = 0
    bare_lines: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not _NUMBER_RE.search(line):
            continue
        number_lines += 1
        if any(token in line for token in GAUGE_TOKENS):
            covered += 1
        else:
            bare_lines.append((line_no, line))
    return NumberLintReport(
        number_lines=number_lines,
        covered=covered,
        bare=len(bare_lines),
        bare_lines=bare_lines,
    )
