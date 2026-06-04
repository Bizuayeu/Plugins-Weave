"""認可済み chat_id allowlist。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable


@dataclass(frozen=True)
class AuthorizedChats:
    """allowlist 化された chat_id の集合。未認可は Domain で破棄、エージェントに渡らない。"""

    chat_ids: FrozenSet[int]

    def is_authorized(self, chat_id: int) -> bool:
        return chat_id in self.chat_ids

    @classmethod
    def from_iterable(cls, ids: Iterable[int]) -> "AuthorizedChats":
        return cls(chat_ids=frozenset(ids))
