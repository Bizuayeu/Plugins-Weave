"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE / ABILITIES / PROFILE / GOALS / STEPS）の Domain 値オブジェクト。

外部依存ゼロ。frozen dataclass + from_dict/to_dict で JSON 相互変換。
バリデーションは __post_init__（不正な enum 値は ValueError）。
役割（秘書/執事/コーチ/アネゴ）の導出は derive_role 純関数（P×A データ駆動判定）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Mapping, Optional

_ROLES = frozenset({"principal", "associate"})
_STATUSES = frozenset({"pending", "active", "blocked"})
_TONES = frozenset({"casual", "polite", "formal"})
_CATEGORIES = frozenset(
    {"family", "friend", "client", "vendor", "employee", "peer", "introducer", "other"}
)
_BIASES = frozenset({"low", "normal", "high"})
_TASK_STATUSES = frozenset({"open", "in_progress", "blocked", "done"})
_PRIORITIES = frozenset({"low", "normal", "high"})
_PROFILE_METHODS = frozenset(
    {"precognitive_viewer", "json_fortune", "mbti", "interview", "observation", "other"}
)
_GOAL_CATEGORIES = frozenset({"money", "work", "relationship", "health", "other"})
_GOAL_STATUSES = frozenset({"active", "paused", "achieved", "abandoned"})
_STEP_STATUSES = frozenset({"todo", "in_progress", "done", "skipped"})

# derive_role の P 判定対象。PROFILE.subject がこの値のレコードだけが
# 「principal 本人の人物理解」としてパーソナライズ軸を立てる
PRINCIPAL_SUBJECT = "principal"


@dataclass(frozen=True)
class Identity:
    category: str = "other"
    relationship_label: str = ""
    honorific: str = ""
    tone: str = "polite"
    context_notes: str = ""
    priority_bias: str = "normal"
    taboo_topics: List[str] = field(default_factory=list)
    shared_with: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.tone not in _TONES:
            raise ValueError(f"invalid tone: {self.tone}")
        if self.category not in _CATEGORIES:
            raise ValueError(f"invalid category: {self.category}")
        if self.priority_bias not in _BIASES:
            raise ValueError(f"invalid priority_bias: {self.priority_bias}")

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Identity":
        return cls(
            category=d.get("category", "other"),
            relationship_label=d.get("relationship_label", ""),
            honorific=d.get("honorific", ""),
            tone=d.get("tone", "polite"),
            context_notes=d.get("context_notes", ""),
            priority_bias=d.get("priority_bias", "normal"),
            taboo_topics=list(d.get("taboo_topics", [])),
            shared_with=list(d.get("shared_with", [])),
        )

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "relationship_label": self.relationship_label,
            "honorific": self.honorific,
            "tone": self.tone,
            "context_notes": self.context_notes,
            "priority_bias": self.priority_bias,
            "taboo_topics": list(self.taboo_topics),
            "shared_with": list(self.shared_with),
        }


@dataclass(frozen=True)
class Individual:
    uuid: str
    display_name: str
    role: str
    status: str
    telegram_chat_id: Optional[int]
    line_user_id: Optional[str]
    identity: Identity
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        if self.role not in _ROLES:
            raise ValueError(f"invalid role: {self.role}")
        if self.status not in _STATUSES:
            raise ValueError(f"invalid status: {self.status}")

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Individual":
        return cls(
            uuid=d["uuid"],
            display_name=d["display_name"],
            role=d["role"],
            status=d["status"],
            telegram_chat_id=d.get("telegram_chat_id"),
            line_user_id=d.get("line_user_id"),
            identity=Identity.from_dict(d.get("identity", {})),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )

    def to_dict(self) -> dict:
        return {
            "uuid": self.uuid,
            "display_name": self.display_name,
            "role": self.role,
            "status": self.status,
            "telegram_chat_id": self.telegram_chat_id,
            "line_user_id": self.line_user_id,
            "identity": self.identity.to_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class Task:
    id: str
    title: str
    status: str
    priority: str
    due_date: Optional[str]
    requester: str
    related_individuals: List[str]
    notes: str
    created_at: str
    updated_at: str
    closed_at: Optional[str]

    def __post_init__(self) -> None:
        if self.status not in _TASK_STATUSES:
            raise ValueError(f"invalid status: {self.status}")
        if self.priority not in _PRIORITIES:
            raise ValueError(f"invalid priority: {self.priority}")

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Task":
        return cls(
            id=d["id"],
            title=d["title"],
            status=d["status"],
            priority=d["priority"],
            due_date=d.get("due_date"),
            requester=d["requester"],
            related_individuals=list(d.get("related_individuals", [])),
            notes=d.get("notes", ""),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            closed_at=d.get("closed_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date,
            "requester": self.requester,
            "related_individuals": list(self.related_individuals),
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
        }


@dataclass(frozen=True)
class Knowledge:
    id: str
    topic: str
    category: str
    content: str
    related: List[str]
    sources: List[str]
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        if not self.topic:
            raise ValueError("knowledge topic must not be empty")

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Knowledge":
        return cls(
            id=d["id"],
            topic=d["topic"],
            category=d.get("category", "general"),
            content=d.get("content", ""),
            related=list(d.get("related", [])),
            sources=list(d.get("sources", [])),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topic": self.topic,
            "category": self.category,
            "content": self.content,
            "related": list(self.related),
            "sources": list(self.sources),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class Ability:
    """秘書が行使できる能力（スキル）の1レコード。

    individuals/tasks/knowledge と同格の管理表だが、外部スキル（例:
    占術鑑定）への発動シグナルと起動ガイダンスを持つ「能力カタログ」。
    秘書は応答前にこれを引いて「何ができるか」を把握する（read 配線は ROUTINE_PROMPT）。
    永続化は registry の git sync で担保し、WAL（言行一致保険）の対象（能力宣言が対外的約束を伴うため、DESIGN §3.8）。
    """

    id: str
    name: str
    trigger: str
    skill_path: str
    guidance: str
    related: List[str]
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ability name must not be empty")

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Ability":
        return cls(
            id=d["id"],
            name=d["name"],
            trigger=d.get("trigger", ""),
            skill_path=d.get("skill_path", ""),
            guidance=d.get("guidance", ""),
            related=list(d.get("related", [])),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "trigger": self.trigger,
            "skill_path": self.skill_path,
            "guidance": self.guidance,
            "related": list(self.related),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class Profile:
    """人物理解の1レコード（パーソナライズ＝P軸データ）。

    占術・性格診断・対話聴取など method 経路で得た解釈を蓄積する
    （precognitive_viewer / json_fortune / mbti / interview / observation）。
    subject="principal" のレコードが1件以上あることが P✓ の判定根拠（derive_role）。
    content は解釈の散文、traits は応答調整に引く特性タグ（DESIGN §3.11）。
    """

    id: str
    subject: str
    method: str
    content: str
    traits: List[str]
    sources: List[str]
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        if not self.subject:
            raise ValueError("profile subject must not be empty")
        if self.method not in _PROFILE_METHODS:
            raise ValueError(f"invalid method: {self.method}")

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Profile":
        return cls(
            id=d["id"],
            subject=d["subject"],
            method=d.get("method", "other"),
            content=d.get("content", ""),
            traits=list(d.get("traits", [])),
            sources=list(d.get("sources", [])),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "method": self.method,
            "content": self.content,
            "traits": list(self.traits),
            "sources": list(self.sources),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class Goal:
    """四大相談コースの目標1件（伴走＝A軸データ）。

    category は相談コース（money/work/relationship/health）。status="active" の
    レコードが1件以上あることが A✓ の判定根拠（derive_role）——全目標が
    achieved/abandoned になると伴走役から降りる（卒業）。逆算の実体は STEPS が持つ。
    """

    id: str
    title: str
    category: str
    status: str
    target_date: Optional[str]
    success_criteria: str
    notes: str
    created_at: str
    updated_at: str
    closed_at: Optional[str]

    def __post_init__(self) -> None:
        if not self.title:
            raise ValueError("goal title must not be empty")
        if self.category not in _GOAL_CATEGORIES:
            raise ValueError(f"invalid category: {self.category}")
        if self.status not in _GOAL_STATUSES:
            raise ValueError(f"invalid status: {self.status}")

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Goal":
        return cls(
            id=d["id"],
            title=d["title"],
            category=d.get("category", "other"),
            status=d.get("status", "active"),
            target_date=d.get("target_date"),
            success_criteria=d.get("success_criteria", ""),
            notes=d.get("notes", ""),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
            closed_at=d.get("closed_at"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "status": self.status,
            "target_date": self.target_date,
            "success_criteria": self.success_criteria,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "closed_at": self.closed_at,
        }


@dataclass(frozen=True)
class Step:
    """目標からの逆算ステップ1件（GOALS の子、goal_id 必須）。

    プロマネ巻き取り（進捗確認・期限ナッジ）の追跡単位。seq は逆算順序。
    TASKS（他者起点の依頼）とはドメインが異なるため別表（DESIGN §3.11）。
    """

    id: str
    goal_id: str
    title: str
    seq: int
    status: str
    due_date: Optional[str]
    notes: str
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        if not self.goal_id:
            raise ValueError("step goal_id must not be empty")
        if self.status not in _STEP_STATUSES:
            raise ValueError(f"invalid status: {self.status}")

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> "Step":
        return cls(
            id=d["id"],
            goal_id=d["goal_id"],
            title=d["title"],
            seq=d.get("seq", 0),
            status=d.get("status", "todo"),
            due_date=d.get("due_date"),
            notes=d.get("notes", ""),
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "title": self.title,
            "seq": self.seq,
            "status": self.status,
            "due_date": self.due_date,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# === 役割導出（P×A データ駆動判定、純関数） ===


@dataclass(frozen=True)
class RoleStatus:
    """P×A 判定の結果。role は秘書の現在の顔（演じ方は SecretaryRole が担う）。"""

    role: str
    personalize: bool
    accompany: bool

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "personalize": self.personalize,
            "accompany": self.accompany,
        }


def derive_role(profiles: List[dict], goals: List[dict]) -> RoleStatus:
    """PROFILE / GOALS のレコードから秘書の役割を決定論的に導出する。

    P = PROFILE に subject="principal" が1件以上（本人の人物理解を預かっている）
    A = GOALS に status="active" が1件以上（進行中の目標を預かっている）

    |        | A なし     | A あり |
    |--------|-----------|--------|
    | P なし | secretary | coach  |
    | P あり | butler    | anego  |

    どの役割かはこの関数（決定論）が決め、どう演じるかは人格ガイダンスが担う
    ——LLM が自称で役割を膨らませる余地を構造的に塞ぐ（DESIGN §3.11）。
    """
    personalize = any(r.get("subject") == PRINCIPAL_SUBJECT for r in profiles)
    accompany = any(r.get("status") == "active" for r in goals)
    role = {
        (False, False): "secretary",
        (True, False): "butler",
        (False, True): "coach",
        (True, True): "anego",
    }[(personalize, accompany)]
    return RoleStatus(role=role, personalize=personalize, accompany=accompany)


# === コレクション操作（純関数、dict ベース） ===


def upsert(records: List[dict], record: dict, key: str) -> List[dict]:
    """key が一致する既存を同位置で置換、なければ末尾に追加。元 list は変更しない。"""
    out = list(records)
    for i, r in enumerate(out):
        if r.get(key) == record.get(key):
            out[i] = record
            return out
    out.append(record)
    return out


def find_by(records: List[dict], key: str, value: Any) -> Optional[dict]:
    """key == value の最初のレコードを返す。無ければ None。"""
    for r in records:
        if r.get(key) == value:
            return r
    return None


def remove_by(records: List[dict], key: str, value: Any) -> List[dict]:
    """key == value のレコードを除いた新 list を返す。元 list は変更しない（upsert と対称）。"""
    return [r for r in records if r.get(key) != value]
