# adapters/scheduler/base.py
"""
スケジューラ基底クラス

SchedulerError は domain.exceptions に移動済み。
後方互換性のため再エクスポート。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from domain.exceptions import SchedulerError

# 後方互換性のため再エクスポート
__all__ = ["BaseSchedulerAdapter", "SchedulerError"]


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
