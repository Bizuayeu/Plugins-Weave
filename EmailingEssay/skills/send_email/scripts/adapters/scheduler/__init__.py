# adapters/scheduler/__init__.py
"""
スケジューラアダプター

OS別のスケジューラ実装を提供する。
"""
import sys
from typing import Union

from .base import SchedulerError, BaseSchedulerAdapter
from .windows import WindowsSchedulerAdapter
from .unix import UnixSchedulerAdapter


def get_scheduler() -> Union[WindowsSchedulerAdapter, UnixSchedulerAdapter]:
    """
    現在のOSに適したスケジューラアダプターを返す。

    Returns:
        スケジューラアダプターのインスタンス
    """
    if sys.platform == "win32":
        return WindowsSchedulerAdapter()
    else:
        return UnixSchedulerAdapter()


__all__ = [
    "get_scheduler",
    "SchedulerError",
    "BaseSchedulerAdapter",
    "WindowsSchedulerAdapter",
    "UnixSchedulerAdapter",
]
