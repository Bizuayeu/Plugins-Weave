"""knowledge の読み取り専用検索（UseCase、I/O を知らない）。

新しい知見を焼く前の「もう在るか」の既出照合は、索引（`id | subjects | topic`）だけでは
足りない——topic に載らない語で書かれた既出は content の中にしか無い。検索の口が無いと
秘書は自前の部分文字列走査を全件に書くことになり（2026-09-12、27 語を 457 件に当てた）、
件数が増えるほど結晶化の律速になる。本モジュールは id / topic / subjects / content に
対する大小無視・NFKC 正規化済みの部分文字列一致を純関数で提供する。出力の有界化
（件数絞り・サイズ申告）は呼び出し側（Interface）の責務。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from domain.normalize import normalize_input


def _haystack(record: Mapping[str, Any]) -> str:
    """検索対象の文字列面を 1 本に畳む（順序は索引と同じ id → subjects → topic → content）。"""
    subjects = " ".join(str(s) for s in record.get("subjects", []) or [])
    joined = "\n".join(
        [
            str(record.get("id", "")),
            subjects,
            str(record.get("topic", "")),
            str(record.get("content", "")),
        ]
    )
    return normalize_input(joined).casefold()


def search_knowledge(
    rows: Sequence[Mapping[str, Any]],
    terms: Sequence[str],
    match_all: bool = True,
) -> list[dict[str, Any]]:
    """`terms` の部分文字列一致で knowledge を絞る（入力順を保ち、複製を返す）。

    照合は両側を NFKC（全角/半角・互換文字）→ casefold に正規化してから行う——「ＬＬＭ」と
    「llm」を別語にすると、既出照合が表記揺れで空振りし重複を焼く側に倒れる。空の語は
    無視し、語が一つも残らなければ 0 件（全件一致にはしない——絞る口が全通しになる穴を
    塞ぐ、`_truncate` の非正幅と同じ理由）。`match_all` は語の合成則：True＝全語一致
    （精査向き）、False＝いずれか一致（同義語を並べた既出照合向き）。検索は観測であって
    検証ではない——該当 0 件はエラーではなく「その語で書かれた知見は無い」という結果。
    """
    needles = [normalize_input(t).casefold() for t in terms if t and t.strip()]
    if not needles:
        return []
    combine = all if match_all else any
    matched = []
    for row in rows:
        hay = _haystack(row)
        if combine(needle in hay for needle in needles):
            matched.append(dict(row))
    return matched
