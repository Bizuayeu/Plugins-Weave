# adapters/scheduler/__init__.py
"""
スケジューラアダプター

OS別のスケジューラ実装を提供する。
"""

import sys

from .base import BaseSchedulerAdapter, SchedulerError
from .unix import UnixSchedulerAdapter
from .windows import WindowsSchedulerAdapter


def get_scheduler() -> BaseSchedulerAdapter:
    """
    現在のOSに適したスケジューラアダプターを返す。

    Returns:
        スケジューラアダプターのインスタンス（SchedulerPort準拠）

    Note:
        Stage 5: 型安全なファクトリー改善
        返り値の型を基底クラスに変更し、factories.pyでのcast()を不要にした。
    """
    if sys.platform == "win32":
        return WindowsSchedulerAdapter()
    else:
        return UnixSchedulerAdapter()


__all__ = [
    "BaseSchedulerAdapter",
    "SchedulerError",
    "UnixSchedulerAdapter",
    "WindowsSchedulerAdapter",
    "get_scheduler",
]
