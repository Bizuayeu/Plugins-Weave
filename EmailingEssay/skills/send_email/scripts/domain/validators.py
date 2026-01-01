# domain/validators.py
"""
データ検証のTypeGuardベースユーティリティ

JSONデータの型安全な検証を提供する。
cast()の代わりにTypeGuardを使用し、破損データの早期検出を実現。
"""

from __future__ import annotations

from typing import Any, TypeGuard

from usecases.ports import ScheduleEntry, WaiterEntry


def is_schedule_entry(obj: Any) -> TypeGuard[ScheduleEntry]:
    """
    ScheduleEntry の型ガード。

    必須フィールド（name, frequency, time）の存在を検証する。

    Args:
        obj: 検証対象のオブジェクト

    Returns:
        有効な ScheduleEntry の場合は True
    """
    if not isinstance(obj, dict):
        return False
    required = {"name", "frequency", "time"}
    return all(k in obj for k in required)


def is_waiter_entry(obj: Any) -> TypeGuard[WaiterEntry]:
    """
    WaiterEntry の型ガード。

    必須フィールド（pid, target_time, theme, registered_at）の存在を検証する。

    Args:
        obj: 検証対象のオブジェクト

    Returns:
        有効な WaiterEntry の場合は True
    """
    if not isinstance(obj, dict):
        return False
    required = {"pid", "target_time", "theme", "registered_at"}
    return all(k in obj for k in required)


def validate_schedule_entries(data: list[Any]) -> list[ScheduleEntry]:
    """
    ScheduleEntry リストを検証・フィルタする。

    不正なエントリは除外され、有効なエントリのみが返される。

    Args:
        data: 検証対象のリスト

    Returns:
        有効な ScheduleEntry のリスト
    """
    return [e for e in data if is_schedule_entry(e)]


def validate_waiter_entries(data: list[Any]) -> list[WaiterEntry]:
    """
    WaiterEntry リストを検証・フィルタする。

    不正なエントリは除外され、有効なエントリのみが返される。

    Args:
        data: 検証対象のリスト

    Returns:
        有効な WaiterEntry のリスト
    """
    return [e for e in data if is_waiter_entry(e)]


# エクスポート
__all__ = [
    "is_schedule_entry",
    "is_waiter_entry",
    "validate_schedule_entries",
    "validate_waiter_entries",
]
