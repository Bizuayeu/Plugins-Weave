# adapters/scheduler/windows.py
"""
Windows Task Scheduler アダプター

schtasksコマンドを使用してWindowsタスクスケジューラを操作する。
"""

from __future__ import annotations

import subprocess
from typing import Any

from domain.constants import (
    ABBR_TO_SCHTASKS,
    ordinal_to_schtasks,
    weekday_to_schtasks,
)
from domain.exceptions import SchedulerError

from .base import BaseSchedulerAdapter

# listメソッドによる組み込みlist型のシャドーイング回避
_List = list


class WindowsSchedulerAdapter(BaseSchedulerAdapter):
    """Windows Task Scheduler のアダプター"""

    # 後方互換性のため残す（constants からインポート推奨）
    DAY_ABBR_MAP = ABBR_TO_SCHTASKS

    def add(
        self,
        task_name: str,
        command: str,
        frequency: str,
        time: str,
        *,
        weekday: str = "",
        day_spec: str = "",
    ) -> None:
        """
        Windows タスクスケジューラにタスクを追加する。

        Args:
            task_name: タスク名
            command: 実行コマンド
            frequency: daily, weekly, monthly
            time: HH:MM形式の時刻
            weekday: 曜日（weekly用）
            day_spec: 日指定（monthly用）

        Raises:
            SchedulerError: タスク作成に失敗した場合
        """

        if frequency == "daily":
            schtasks_cmd = self._build_daily_command(task_name, command, time)
        elif frequency == "weekly":
            schtasks_cmd = self._build_weekly_command(task_name, command, time, weekday)
        elif frequency == "monthly":
            schtasks_cmd = self._build_monthly_command(task_name, command, time, day_spec)
        else:
            raise SchedulerError(f"Unknown frequency: {frequency}")

        self._execute_schtasks(schtasks_cmd)

    def remove(self, name: str) -> None:
        """
        タスクを削除する。

        Args:
            name: タスク名

        Raises:
            SchedulerError: 削除に失敗した場合
        """
        schtasks_cmd = ["schtasks", "/delete", "/tn", name, "/f"]
        result = subprocess.run(schtasks_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise SchedulerError(f"Failed to delete task: {result.stderr}")

    def list(self, known_names: _List[str] | None = None) -> _List[dict[str, Any]]:
        """
        Essay_で始まるタスク、および指定されたタスク名の一覧を取得する。

        Args:
            known_names: 追加で検索する既知のタスク名リスト

        Returns:
            タスク情報のリスト
        """
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "CSV"], capture_output=True, text=True
        )

        search_names = set(known_names or [])
        tasks = []
        for line in result.stdout.split("\n"):
            # Essay_プレフィックスまたは既知の名前にマッチ
            if "Essay_" in line or any(name in line for name in search_names):
                parts = line.strip().strip('"').split('","')
                if parts:
                    task_name = parts[0].replace('"', '').lstrip('\\')
                    tasks.append({"name": task_name})
        return tasks

    def _build_daily_command(self, task_name: str, command: str, time: str) -> _List[str]:
        """日次タスクのschtasksコマンドを構築する。"""
        return [
            "schtasks",
            "/create",
            "/tn",
            task_name,
            "/tr",
            command,
            "/sc",
            "daily",
            "/st",
            time,
            "/f",
        ]

    def _build_weekly_command(
        self, task_name: str, command: str, time: str, weekday: str
    ) -> _List[str]:
        """週次タスクのschtasksコマンドを構築する。"""
        try:
            day = weekday_to_schtasks(weekday)
        except ValueError:
            day = "MON"  # フォールバック
        return [
            "schtasks",
            "/create",
            "/tn",
            task_name,
            "/tr",
            command,
            "/sc",
            "weekly",
            "/d",
            day,
            "/st",
            time,
            "/f",
        ]

    def _build_monthly_command(
        self, task_name: str, command: str, time: str, day_spec: str
    ) -> _List[str]:
        """月次タスクのschtasksコマンドを構築する。"""
        from domain.models import MonthlyPattern, MonthlyType

        pattern = MonthlyPattern.parse(day_spec)

        if pattern.type == MonthlyType.DATE:
            return [
                "schtasks",
                "/create",
                "/tn",
                task_name,
                "/tr",
                command,
                "/sc",
                "monthly",
                "/d",
                str(pattern.day_num),
                "/st",
                time,
                "/f",
            ]
        elif pattern.type == MonthlyType.NTH_WEEKDAY:
            weekday_str = pattern.weekday if pattern.weekday is not None else ""
            weekday_abbr = ABBR_TO_SCHTASKS.get(weekday_str, "MON")
            try:
                ordinal_val = pattern.ordinal if pattern.ordinal is not None else 1
                week_ordinal = ordinal_to_schtasks(ordinal_val)
            except ValueError:
                week_ordinal = "FIRST"
            return [
                "schtasks",
                "/create",
                "/tn",
                task_name,
                "/tr",
                command,
                "/sc",
                "monthly",
                "/mo",
                week_ordinal,
                "/d",
                weekday_abbr,
                "/st",
                time,
                "/f",
            ]
        elif pattern.type == MonthlyType.LAST_WEEKDAY:
            weekday_str = pattern.weekday if pattern.weekday is not None else ""
            weekday_abbr = ABBR_TO_SCHTASKS.get(weekday_str, "MON")
            return [
                "schtasks",
                "/create",
                "/tn",
                task_name,
                "/tr",
                command,
                "/sc",
                "monthly",
                "/mo",
                "LAST",
                "/d",
                weekday_abbr,
                "/st",
                time,
                "/f",
            ]
        elif pattern.type == MonthlyType.LAST_DAY:
            # 月末は日次タスク + ランナースクリプトで対応（上位層で処理）
            raise SchedulerError("last_day requires runner script (handled by caller)")
        else:
            raise SchedulerError(f"Unknown monthly type: {pattern.type}")

    def _execute_schtasks(self, cmd: _List[str]) -> None:
        """schtasksコマンドを実行する。"""
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise SchedulerError(f"Failed to create task: {result.stderr}")
