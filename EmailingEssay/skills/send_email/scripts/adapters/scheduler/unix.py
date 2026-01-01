# adapters/scheduler/unix.py
"""
Unix (Linux/macOS) Cron アダプター

crontabコマンドを使用してcronジョブを操作する。
"""
from __future__ import annotations

import subprocess
from typing import Any

from domain.constants import weekday_to_cron
from domain.exceptions import SchedulerError
from .base import BaseSchedulerAdapter


class UnixSchedulerAdapter(BaseSchedulerAdapter):
    """Unix Cron のアダプター"""

    def add(
        self,
        task_name: str,
        command: str,
        frequency: str,
        time: str,
        **kwargs: Any
    ) -> None:
        """
        Cronエントリを追加する。

        Args:
            task_name: タスク名（コメントとして使用）
            command: 実行コマンド
            frequency: daily, weekly, monthly
            time: HH:MM形式の時刻
            **kwargs: weekday, day_spec など

        Raises:
            SchedulerError: crontab更新に失敗した場合
        """
        weekday = kwargs.get("weekday", "")
        day_spec = kwargs.get("day_spec", "")

        hour, minute = time.split(":")
        cron_line = self._build_cron_line(
            frequency, hour, minute, command, weekday, day_spec
        )

        # 既存のcrontabを取得
        current = self._get_current_crontab()

        # 新しいエントリを追加（コメント付き）
        new_entry = f"# {task_name}\n{cron_line}"
        updated = current + "\n" + new_entry if current else new_entry

        # crontabを更新
        self._set_crontab(updated)

    def remove(self, name: str) -> None:
        """
        Cronエントリを削除する。

        Args:
            name: タスク名（コメントから検索）

        Raises:
            SchedulerError: 削除に失敗した場合
        """
        current = self._get_current_crontab()
        if not current:
            return

        lines = current.split("\n")
        new_lines = []
        skip_next = False

        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if name in line and line.strip().startswith("#"):
                skip_next = True  # 次の行（実際のcronエントリ）もスキップ
                continue
            new_lines.append(line)

        self._set_crontab("\n".join(new_lines))

    def list(self) -> list[dict[str, Any]]:
        """
        Essay_で始まるCronエントリ一覧を取得する。

        Returns:
            エントリ情報のリスト
        """
        current = self._get_current_crontab()
        if not current:
            return []

        tasks = []
        lines = current.split("\n")

        for i, line in enumerate(lines):
            if "Essay_" in line and line.strip().startswith("#"):
                task_name = line.strip().lstrip("# ")
                tasks.append({"name": task_name})

        return tasks

    def _build_cron_line(
        self,
        frequency: str,
        hour: str,
        minute: str,
        command: str,
        weekday: str = "",
        day_spec: str = ""
    ) -> str:
        """Cronエントリの行を構築する。"""
        if frequency == "daily":
            return f"{minute} {hour} * * * {command}"
        elif frequency == "weekly":
            day_num = self._weekday_to_cron_num(weekday)
            return f"{minute} {hour} * * {day_num} {command}"
        elif frequency == "monthly":
            # 月次はランナースクリプトで対応するため、日次でチェック
            # 上位層でランナースクリプトを作成し、そのパスをcommandとして渡す
            return f"{minute} {hour} * * * {command}"
        else:
            raise SchedulerError(f"Unknown frequency: {frequency}")

    def _weekday_to_cron_num(self, weekday: str) -> int:
        """曜日をcron番号に変換する（0=日曜）。"""
        try:
            return weekday_to_cron(weekday)
        except ValueError:
            return 1  # デフォルト: 月曜

    def _get_current_crontab(self) -> str:
        """現在のcrontabを取得する。"""
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            # crontabが存在しない場合は空を返す
            return ""
        return result.stdout.strip()

    def _set_crontab(self, content: str) -> None:
        """crontabを設定する。"""
        proc = subprocess.Popen(
            ["crontab", "-"],
            stdin=subprocess.PIPE,
            text=True
        )
        proc.communicate(input=content)
        if proc.returncode != 0:
            raise SchedulerError("Failed to update crontab")
