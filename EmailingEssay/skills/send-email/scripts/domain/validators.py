# domain/validators.py
"""
データ検証のTypeGuardベースユーティリティ

JSONデータの型安全な検証を提供する。
cast()の代わりにTypeGuardを使用し、破損データの早期検出を実現。
"""

from __future__ import annotations

from typing import Any, TypeGuard

from usecases.ports import ScheduleEntry, WaiterEntry

from .models import LedgerRecord, ReplyRecord

# 台帳・返信レコードの必須フィールド（いずれも str）
_LEDGER_REQUIRED = ("message_id", "sent_at", "subject", "recipient", "body_file")
_REPLY_REQUIRED = (
    "message_id",
    "in_reply_to",
    "sender",
    "received_at",
    "body",
    "content_class",
)


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


def _has_str_fields(obj: Any, required: tuple[str, ...]) -> bool:
    """必須フィールドが全て str として存在するか検証する。"""
    if not isinstance(obj, dict):
        return False
    return all(isinstance(obj.get(k), str) for k in required)


def validate_ledger_records(data: list[Any]) -> list[LedgerRecord]:
    """
    台帳レコードのリストを検証・変換する。

    破損・型不正なエントリは除外され、有効なものだけが返される
    （JSONL の 1 行が壊れても残りを読めるようにするため）。

    Args:
        data: 検証対象のリスト（JSONL をパースした生の値）

    Returns:
        有効な LedgerRecord のリスト
    """
    return [
        LedgerRecord.from_dict(e) for e in data if _has_str_fields(e, _LEDGER_REQUIRED)
    ]


def validate_reply_records(data: list[Any]) -> list[ReplyRecord]:
    """
    返信レコードのリストを検証・変換する。

    破損・型不正なエントリは除外される。素性表明（content_class）を
    欠いたエントリも不正として落とす。

    Args:
        data: 検証対象のリスト（JSONL をパースした生の値）

    Returns:
        有効な ReplyRecord のリスト
    """
    return [
        ReplyRecord.from_dict(e) for e in data if _has_str_fields(e, _REPLY_REQUIRED)
    ]


# エクスポート
__all__ = [
    "is_schedule_entry",
    "is_waiter_entry",
    "validate_ledger_records",
    "validate_reply_records",
    "validate_schedule_entries",
    "validate_waiter_entries",
]
