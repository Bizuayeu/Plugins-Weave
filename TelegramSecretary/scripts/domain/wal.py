"""WAL（Write-Ahead Log）の Domain 値オブジェクトと純関数。

外部依存ゼロ（I/O も git も時計も持たない）。registry.py（frozen dataclass +
__post_init__ 検証 + from_dict/to_dict + 純関数）と lease.py（now を引数で受ける
時計非依存）のパターンを踏襲する。

- WalEntry: 1 intent の値オブジェクト（key/kind/status/payload/created_at）
- reconcile: pending のうち registry に無い (kind, key)＝やり残しを抽出（redo 対象）
- settle: registry に存在する pending を done 化（正常反映済み intent の累積を防ぐ）
- settle_outbound: 指定 key の outbound pending を done 化（外部真実源の無い能動送信の happy-path settle）
- quarantine: 検証に落ちた pending を理由付きで dead へ隔離（redo の道連れを断つ）
- checkpoint: pending / dead は無条件保持、done は retention で掃除
  （WAL〔整合性〕と短期記憶〔直近 retention の会話文脈〕の二役を一手に引き受ける）
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

_WAL_STATUSES = frozenset({"pending", "done", "dead"})


@dataclass(frozen=True)
class WalEntry:
    """WAL ログ 1 行。registry への intent（kind/key/payload）と処理状態（status）。

    - key: registry のキー（individuals=uuid, tasks=id, knowledge=id, abilities=id）
    - kind: 対象管理表（"individuals" / "tasks" / "knowledge" / "abilities"）。同 key でも kind で区別
    - status: "pending"（未確認）/ "done"（registry 反映済み）/ "dead"（検証に落ちて隔離）
    - payload: registry へ upsert するレコード dict
    - created_at: ISO 8601（tz aware）文字列。checkpoint の retention 判定に使う
    - reason: dead の隔離理由。空文字なら to_dict に載せない（既存 WAL.jsonl と byte 互換）
    """

    key: str
    kind: str
    status: str
    payload: dict
    created_at: str
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status not in _WAL_STATUSES:
            raise ValueError(f"invalid wal status: {self.status}")

    def mark_done(self) -> WalEntry:
        """status を done にした新しい entry を返す（frozen ゆえコピー）。

        dead から done へ治癒する場合も reason は引き継ぐ（なぜ一度落ちたかの証跡を残す）。
        """
        return WalEntry(
            key=self.key,
            kind=self.kind,
            status="done",
            payload=self.payload,
            created_at=self.created_at,
            reason=self.reason,
        )

    def mark_dead(self, reason: str) -> WalEntry:
        """status を dead にし理由を添えた新しい entry を返す（mark_done と同型）。

        dead は redo ソースではないが「果たされていない約束」の記録なので checkpoint で
        消さない。出口は同 key の再登録（settle が done 化）か wal-drop の二つだけ。
        """
        return WalEntry(
            key=self.key,
            kind=self.kind,
            status="dead",
            payload=self.payload,
            created_at=self.created_at,
            reason=reason,
        )

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> WalEntry:
        return cls(
            key=d["key"],
            kind=d["kind"],
            status=d["status"],
            payload=dict(d.get("payload", {})),
            created_at=d["created_at"],
            reason=d.get("reason", ""),
        )

    def to_dict(self) -> dict:
        d = {
            "key": self.key,
            "kind": self.kind,
            "status": self.status,
            "payload": dict(self.payload),
            "created_at": self.created_at,
        }
        if self.reason:
            d["reason"] = self.reason
        return d


def reconcile(
    entries: list[WalEntry], registry_keys: set[tuple[str, str]]
) -> list[WalEntry]:
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
    entries: list[WalEntry], registry_keys: set[tuple[str, str]]
) -> list[WalEntry]:
    """registry に (kind, key) が存在する pending / dead を done 化（reconcile の補集合を畳む）。

    既存 done と、registry に無い pending（やり残し）・dead（隔離中）はそのまま返す（順序保持）。
    これを redo 後に適用することで「正常反映済みなのに pending のまま無限累積」を防ぐ。
    dead も対象にするのは自己治癒のため——同 key の正しい add が入れば、隔離された約束は
    実体を伴ったことになるので畳んでよい。
    """
    out: list[WalEntry] = []
    for e in entries:
        if e.status in ("pending", "dead") and (e.kind, e.key) in registry_keys:
            out.append(e.mark_done())
        else:
            out.append(e)
    return out


def settle_outbound(entries: list[WalEntry], key: str) -> list[WalEntry]:
    """指定 key の outbound pending を done 化（happy-path settle）。

    registry kind の settle が registry_keys 照合で done 化するのに対し、outbound は
    照合先（外部真実源）を持たないため、**送信に成功した本人が key 直指定で done 化**する。
    redo（起動時の at-least-once 再送）を待たず即 done にすることで「成功送信が次回起動で
    再送される」のを断つ。kind != "outbound" / key 不一致 / 既 done は不変・順序保持。
    """
    out: list[WalEntry] = []
    for e in entries:
        if e.kind == "outbound" and e.key == key and e.status == "pending":
            out.append(e.mark_done())
        else:
            out.append(e)
    return out


def quarantine(
    entries: list[WalEntry], failures: Mapping[tuple[str, str], str]
) -> list[WalEntry]:
    """検証に落ちた pending を、理由付きで dead へ隔離する。

    failures は (kind, key) -> reason。該当する pending だけを差し替え、他は不変・順序保持
    （settle_outbound と同じ書き方）。done は対象外——既に registry へ反映済みのものを
    後から dead に落とさない。1 件の不正が他の pending の redo を道連れにしないための操作。
    """
    out: list[WalEntry] = []
    for e in entries:
        reason = failures.get((e.kind, e.key))
        if e.status == "pending" and reason is not None:
            out.append(e.mark_dead(reason))
        else:
            out.append(e)
    return out


def checkpoint(
    entries: list[WalEntry], now: datetime, retention_h: int = 24
) -> list[WalEntry]:
    """pending / dead は無条件保持、done は created_at が retention より古ければ掃除。

    終了処理でなく起動時に呼ぶ（強制終了で終了処理は飛ぶため）。pending を消さないことが
    整合性の要、done を時間で畳むことが短期記憶のローテーション。dead は redo ソースでは
    ないが「果たされていない約束」の記録なので消さない——出口は同 key の再登録（settle）か
    wal-drop だけで、時間では畳まれない。
    """
    cutoff = now - timedelta(hours=retention_h)
    out: list[WalEntry] = []
    for e in entries:
        if e.status != "done" or datetime.fromisoformat(e.created_at) >= cutoff:
            out.append(e)
    return out
