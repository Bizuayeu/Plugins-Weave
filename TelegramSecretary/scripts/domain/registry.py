"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE / ABILITIES）の Domain 値オブジェクト。

外部依存ゼロ。frozen dataclass + from_dict/to_dict で JSON 相互変換。
バリデーションは __post_init__（不正な enum 値は ValueError）。
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
