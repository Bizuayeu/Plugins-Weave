"""WAL（Write-Ahead Log）の Domain 値オブジェクトと純関数。

外部依存ゼロ（I/O も git も時計も持たない）。registry.py（frozen dataclass +
__post_init__ 検証 + from_dict/to_dict + 純関数）と lease.py（now を引数で受ける
時計非依存）のパターンを踏襲する。

- WalEntry: 1 intent の値オブジェクト（key/kind/status/payload/created_at）
- reconcile: pending のうち registry に無い (kind, key)＝やり残しを抽出（redo 対象）
- settle: registry に存在する pending を done 化（正常反映済み intent の累積を防ぐ）
- checkpoint: pending は無条件保持（redo ソース）、done は retention で掃除
  （WAL〔整合性〕と短期記憶〔直近 retention の会話文脈〕の二役を一手に引き受ける）
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Mapping, Set, Tuple

_WAL_STATUSES = frozenset({"pending", "done"})


@dataclass(frozen=True)
class WalEntry:
    """WAL ログ 1 行。registry への intent（kind/key/payload）と処理状態（status）。

    - key: registry のキー（individuals=uuid, tasks=id, knowledge=id, abilities=id）
    - kind: 対象管理表（"individuals" / "tasks" / "knowledge" / "abilities"）。同 key でも kind で区別
    - status: "pending"（未確認）/ "done"（registry 反映済み）
    - payload: registry へ upsert するレコード dict
    - created_at: ISO 8601（tz aware）文字列。checkpoint の retention 判定に使う
    """

    key: str
    kind: str
    status: str
    payload: dict
    created_at: str

    def __post_init__(self) -> None:
        if self.status not in _WAL_STATUSES:
            raise ValueError(f"invalid wal status: {self.status}")

    def mark_done(self) -> "WalEntry":
        """status を done にした新しい entry を返す（frozen ゆえコピー）。"""
        return WalEntry(
            key=self.key,
            kind=self.kind,
            status="done",
            payload=self.payload,
            created_at=self.created_at,
        )

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "WalEntry":
        return cls(
            key=d["key"],
            kind=d["kind"],
            status=d["status"],
            payload=dict(d.get("payload", {})),
            created_at=d["created_at"],
        )

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "kind": self.kind,
            "status": self.status,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }


def reconcile(
    entries: List[WalEntry], registry_keys: Set[Tuple[str, str]]
) -> List[WalEntry]:
    """pending のうち (kind, key) が registry に無いもの＝やり残しを返す。

    done は対象外（既に処理済み）。registry_keys は (kind, key) のセットで、
    kind を跨いだ key 衝突（tasks T0001 と individuals T0001）を区別する。
    """
    return [
        e
        for e in entries
        if e.status == "pending" and (e.kind, e.key) not in registry_keys
    ]


def settle(
    entries: List[WalEntry], registry_keys: Set[Tuple[str, str]]
) -> List[WalEntry]:
    """registry に (kind, key) が存在する pending を done 化（reconcile の補集合を畳む）。

    既存 done と、registry に無い pending（やり残し）はそのまま返す（順序保持）。
    これを redo 後に適用することで「正常反映済みなのに pending のまま無限累積」を防ぐ。
    """
    out: List[WalEntry] = []
    for e in entries:
        if e.status == "pending" and (e.kind, e.key) in registry_keys:
            out.append(e.mark_done())
        else:
            out.append(e)
    return out


def checkpoint(
    entries: List[WalEntry], now: datetime, retention_h: int = 24
) -> List[WalEntry]:
    """pending は無条件保持（redo ソース）、done は created_at が retention より古ければ掃除。

    終了処理でなく起動時に呼ぶ（強制終了で終了処理は飛ぶため）。pending を消さないことが
    整合性の要、done を時間で畳むことが短期記憶のローテーション。
    """
    cutoff = now - timedelta(hours=retention_h)
    out: List[WalEntry] = []
    for e in entries:
        if e.status == "pending":
            out.append(e)
        elif datetime.fromisoformat(e.created_at) >= cutoff:
            out.append(e)
    return out
