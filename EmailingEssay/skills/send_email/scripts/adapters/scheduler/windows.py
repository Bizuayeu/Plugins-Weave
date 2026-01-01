# adapters/scheduler/windows.py
"""
Windows Task Scheduler アダプター

schtasksコマンドを使用してWindowsタスクスケジューラを操作する。
"""
from __future__ import annotations

import subprocess
from typing import Any

from .base import BaseSchedulerAdapter, SchedulerError


class WindowsSchedulerAdapter(BaseSchedulerAdapter):
    """Windows Task Scheduler のアダプター"""

    # 曜日の略称マップ
    DAY_ABBR_MAP = {
        "mon": "MON", "tue": "TUE", "wed": "WED",
        "thu": "THU", "fri": "FRI", "sat": "SAT", "sun": "SUN"
    }
    DAY_FULL_MAP = {
        "monday": "MON", "tuesday": "TUE", "wednesday": "WED",
        "thursday": "THU", "friday": "FRI", "saturday": "SAT", "sunday": "SUN"
    }
    WEEK_ORD_MAP = {1: "FIRST", 2: "SECOND", 3: "THIRD", 4: "FOURTH"}

    def add(
        self,
        task_name: str,
        command: str,
        frequency: str,
        time: str,
        **kwargs: Any
    ) -> None:
        """
        Windows タスクスケジューラにタスクを追加する。

        Args:
            task_name: タスク名
            command: 実行コマンド
            frequency: daily, weekly, monthly
            time: HH:MM形式の時刻
            **kwargs: weekday, day_spec など

        Raises:
            SchedulerError: タスク作成に失敗した場合
        """
        weekday = kwargs.get("weekday", "")
        day_spec = kwargs.get("day_spec", "")

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

    def list(self) -> list[dict[str, Any]]:
        """
        Essay_で始まるタスク一覧を取得する。

        Returns:
            タスク情報のリスト
        """
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "CSV"],
            capture_output=True, text=True
        )

        tasks = []
        for line in result.stdout.split("\n"):
            if "Essay_" in line:
                parts = line.strip().strip('"').split('","')
                if parts:
                    task_name = parts[0].replace('"', '').lstrip('\\')
                    tasks.append({"name": task_name})
        return tasks

    def _build_daily_command(self, task_name: str, command: str, time: str) -> list[str]:
        """日次タスクのschtasksコマンドを構築"""
        return [
            "schtasks", "/create", "/tn", task_name,
            "/tr", command,
            "/sc", "daily",
            "/st", time,
            "/f"
        ]

    def _build_weekly_command(
        self, task_name: str, command: str, time: str, weekday: str
    ) -> list[str]:
        """週次タスクのschtasksコマンドを構築"""
        day = self.DAY_FULL_MAP.get(
            weekday.lower(),
            self.DAY_ABBR_MAP.get(weekday.lower(), "MON")
        )
        return [
            "schtasks", "/create", "/tn", task_name,
            "/tr", command,
            "/sc", "weekly",
            "/d", day,
            "/st", time,
            "/f"
        ]

    def _build_monthly_command(
        self, task_name: str, command: str, time: str, day_spec: str
    ) -> list[str]:
        """月次タスクのschtasksコマンドを構築"""
        from domain.models import MonthlyPattern, MonthlyType

        pattern = MonthlyPattern.parse(day_spec)

        if pattern.type == MonthlyType.DATE:
            return [
                "schtasks", "/create", "/tn", task_name,
                "/tr", command,
                "/sc", "monthly",
                "/d", str(pattern.day_num),
                "/st", time,
                "/f"
            ]
        elif pattern.type == MonthlyType.NTH_WEEKDAY:
            weekday_abbr = self.DAY_ABBR_MAP.get(pattern.weekday, "MON")
            week_ordinal = self.WEEK_ORD_MAP.get(pattern.ordinal, "FIRST")
            return [
                "schtasks", "/create", "/tn", task_name,
                "/tr", command,
                "/sc", "monthly",
                "/mo", week_ordinal,
                "/d", weekday_abbr,
                "/st", time,
                "/f"
            ]
        elif pattern.type == MonthlyType.LAST_WEEKDAY:
            weekday_abbr = self.DAY_ABBR_MAP.get(pattern.weekday, "MON")
            return [
                "schtasks", "/create", "/tn", task_name,
                "/tr", command,
                "/sc", "monthly",
                "/mo", "LAST",
                "/d", weekday_abbr,
                "/st", time,
                "/f"
            ]
        elif pattern.type == MonthlyType.LAST_DAY:
            # 月末は日次タスク + ランナースクリプトで対応（上位層で処理）
            raise SchedulerError("last_day requires runner script (handled by caller)")
        else:
            raise SchedulerError(f"Unknown monthly type: {pattern.type}")

    def _execute_schtasks(self, cmd: list[str]) -> None:
        """schtasksコマンドを実行"""
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise SchedulerError(f"Failed to create task: {result.stderr}")
