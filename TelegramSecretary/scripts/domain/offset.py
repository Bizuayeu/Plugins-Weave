"""Telegram getUpdates の offset 単調増加値オブジェクト。"""
from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import InvalidOffsetError


@dataclass(frozen=True)
class UpdateOffset:
    """次回 getUpdates で渡す offset 値。単調増加が保証される。"""

    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise InvalidOffsetError(f"offset must be >= 0, got {self.value}")

    def advance(self, update_id: int) -> "UpdateOffset":
        """update_id を消費した後の次回 offset を返す。常に max(current, id+1) で単調増加。"""
        return UpdateOffset(value=max(self.value, update_id + 1))

    @classmethod
    def initial(cls) -> "UpdateOffset":
        return cls(value=0)
