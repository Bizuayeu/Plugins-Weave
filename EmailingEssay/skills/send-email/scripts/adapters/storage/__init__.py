# adapters/storage/__init__.py
"""
ストレージアダプター

スケジュール情報の永続化を管理する。

Stage 5: 責務分離
- LedgerStorageAdapter: 送信台帳の永続化（Stage 2）
- PathResolverAdapter: パス解決
- ScheduleStorageAdapter: スケジュール永続化
- WaiterStorageAdapter: 待機プロセス追跡
"""

from .ledger_storage import LedgerStorageAdapter
from .path_resolver import PathResolverAdapter
from .schedule_storage import ScheduleStorageAdapter
from .waiter_storage import WaiterStorageAdapter

__all__ = [
    "LedgerStorageAdapter",
    "PathResolverAdapter",
    "ScheduleStorageAdapter",
    "WaiterStorageAdapter",
]
