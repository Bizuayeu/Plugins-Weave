# adapters/scheduler/base.py
"""
スケジューラ基底クラスとエラー定義
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class SchedulerError(Exception):
    """スケジューラ操作エラー"""
    pass


class BaseSchedulerAdapter(ABC):
    """スケジューラアダプターの基底クラス"""

    @abstractmethod
    def add(
        self,
        task_name: str,
        command: str,
        frequency: str,
        time: str,
        **kwargs: Any
    ) -> None:
        """スケジュールを追加する"""
        pass

    @abstractmethod
    def remove(self, name: str) -> None:
        """スケジュールを削除する"""
        pass

    @abstractmethod
    def list(self) -> list[dict[str, Any]]:
        """スケジュール一覧を取得する"""
        pass
