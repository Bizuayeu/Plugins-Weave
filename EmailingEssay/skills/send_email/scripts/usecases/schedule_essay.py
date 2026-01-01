# usecases/schedule_essay.py
"""
スケジュールエッセイユースケース

定期的なエッセイ配信のスケジュール管理を行う。
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from domain.models import MonthlyPattern, MonthlyType
from domain.constants import WEEKDAYS_FULL, VALID_WEEKDAYS
from frameworks.logging_config import get_logger

if TYPE_CHECKING:
    from .ports import SchedulerPort, StoragePort

logger = get_logger("schedule")


class ScheduleEssayUseCase:
    """スケジュール管理ユースケース"""

    def __init__(self, scheduler_port: "SchedulerPort", storage_port: "StoragePort") -> None:
        """
        Args:
            scheduler_port: SchedulerPort実装
            storage_port: StoragePort実装
        """
        self._scheduler = scheduler_port
        self._storage = storage_port

    def add(
        self,
        frequency: str,
        time_spec: str,
        weekday: str = "",
        theme: str = "",
        context_file: str = "",
        file_list: str = "",
        lang: str = "",
        name: str = "",
        day_spec: str = ""
    ) -> None:
        """
        スケジュールを追加する。

        トランザクション的に動作し、途中で失敗した場合はロールバックする。

        Args:
            frequency: daily, weekly, monthly
            time_spec: HH:MM形式の時刻
            weekday: 曜日（weekly用）
            theme: エッセイテーマ
            context_file: コンテキストファイルパス
            file_list: ファイルリストパス
            lang: 言語（ja, en, auto）
            name: カスタムタスク名
            day_spec: 月間パターン指定（monthly用）
        """
        # バリデーション
        self._validate_frequency(frequency)
        self._validate_weekday(frequency, weekday)
        monthly_type = self._validate_day_spec(frequency, day_spec)
        self._validate_time(time_spec)

        # タスク名生成
        task_name = self._generate_task_name(frequency, time_spec, theme, name, day_spec)
        command = self._build_claude_command(theme, context_file, file_list, lang)

        # トランザクション的に実行
        scheduler_registered = False

        try:
            # Step 1: OSスケジューラに登録
            self._create_os_schedule(
                task_name, command, frequency, time_spec,
                weekday=weekday, day_spec=day_spec, monthly_type=monthly_type
            )
            scheduler_registered = True

            # Step 2: JSONバックアップに保存
            self._save_schedule_entry(
                task_name, frequency, time_spec, weekday, theme,
                context_file, file_list, lang, day_spec, monthly_type
            )

            # Step 3: 確認メッセージ
            self._print_confirmation(
                task_name, frequency, time_spec, weekday, theme,
                context_file, file_list, lang, day_spec
            )

        except Exception as e:
            # ロールバック：スケジューラ登録を取り消す
            if scheduler_registered:
                try:
                    self._scheduler.remove(task_name)
                except Exception:
                    pass  # ロールバック失敗は無視（元の例外を優先）
            raise

    def list(self) -> None:
        """登録済みスケジュールを一覧表示する。"""
        # OSスケジューラから取得
        os_tasks = self._scheduler.list()
        os_task_names = {t["name"] for t in os_tasks}

        # JSONバックアップから取得
        schedules = self._storage.load_schedules()

        if not schedules and not os_tasks:
            print("No schedules found.")
            return

        print("Registered schedules:")
        print("-" * 60)

        for sched in schedules:
            status = "active" if sched["name"] in os_task_names else "orphaned"
            freq_str = sched["frequency"]
            if sched.get("day_spec"):
                freq_str += f" ({sched['day_spec']})"
            elif sched.get("weekday"):
                freq_str += f" ({sched['weekday']})"

            print(f"  {sched['name']}")
            print(f"    Frequency: {freq_str} at {sched['time']}")
            if sched.get("theme"):
                print(f"    Theme: {sched['theme']}")
            if sched.get("context"):
                print(f"    Context: {sched['context']}")
            if sched.get("lang"):
                print(f"    Language: {sched['lang']}")
            print(f"    Status: {status}")
            print()

        # OS側のみにあるタスク
        json_names = {s["name"] for s in schedules}
        os_only = [t["name"] for t in os_tasks if t["name"] not in json_names]
        if os_only:
            print("OS-only tasks (not in backup):")
            for t in os_only:
                print(f"  {t}")

    def remove(self, name: str) -> None:
        """
        スケジュールを削除する。

        Args:
            name: タスク名
        """
        # OSスケジューラから削除
        try:
            self._scheduler.remove(name)
        except Exception as e:
            logger.warning(f"Could not remove from OS scheduler: {e}")

        # ランナースクリプトがあれば削除
        self._remove_runner_script(name)

        # JSONから削除
        schedules = self._storage.load_schedules()
        original_count = len(schedules)
        schedules = [s for s in schedules if s.get("name") != name]

        if len(schedules) < original_count:
            self._storage.save_schedules(schedules)
            print(f"Removed schedule: {name}")
        else:
            print(f"Schedule not found in backup: {name}")

    # Private methods

    def _validate_frequency(self, frequency: str) -> None:
        """頻度のバリデーション"""
        if frequency not in ["daily", "weekly", "monthly"]:
            raise ValueError(f"frequency must be 'daily', 'weekly', or 'monthly', got '{frequency}'")

    def _validate_weekday(self, frequency: str, weekday: str) -> None:
        """曜日のバリデーション（weekly用）"""
        if frequency == "weekly" and weekday.lower() not in WEEKDAYS_FULL:
            raise ValueError(f"weekday must be one of {WEEKDAYS_FULL}")

    def _validate_day_spec(self, frequency: str, day_spec: str) -> str:
        """day_specのバリデーション（monthly用）"""
        if frequency != "monthly":
            return ""
        if not day_spec:
            raise ValueError("monthly schedules require day_spec (e.g., 15, 3rd_wed, last_fri, last_day)")

        pattern = MonthlyPattern.parse(day_spec)
        return pattern.type.value

    def _validate_time(self, time_spec: str) -> None:
        """時刻形式のバリデーション"""
        try:
            datetime.strptime(time_spec, "%H:%M")
        except ValueError:
            raise ValueError(f"time must be in HH:MM format, got '{time_spec}'")

    def _generate_task_name(
        self, frequency: str, time_spec: str, theme: str, name: str, day_spec: str
    ) -> str:
        """タスク名を生成"""
        if name:
            return name
        if frequency == "monthly" and day_spec:
            base = theme if theme else f"{frequency}_{day_spec}_{time_spec.replace(':', '')}"
        else:
            base = theme if theme else f"{frequency}_{time_spec.replace(':', '')}"
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in base)
        return f"Essay_{safe_name}"

    def _build_claude_command(
        self, theme: str = "", context_file: str = "", file_list: str = "", lang: str = ""
    ) -> str:
        """Claudeコマンドを構築"""
        args = []

        if sys.platform == "win32":
            q = '\\"'
        else:
            q = "'"

        if theme:
            args.append(f'{q}{theme}{q}')
        if context_file:
            args.append(f'-c {q}{context_file}{q}')
        if file_list:
            args.append(f'-f {q}{file_list}{q}')
        if lang:
            args.append(f'-l {lang}')
        args_str = " ".join(args)

        if sys.platform == "win32":
            claude_path = os.path.expanduser("~/.local/bin/claude.exe")
            return f'"{claude_path}" --dangerously-skip-permissions -p "/essay {args_str}"'
        return f'claude --dangerously-skip-permissions -p "/essay {args_str}"'

    def _create_os_schedule(
        self,
        task_name: str,
        command: str,
        frequency: str,
        time_spec: str,
        weekday: str = "",
        day_spec: str = "",
        monthly_type: str = ""
    ) -> None:
        """OSスケジューラにタスクを登録"""
        if frequency == "monthly" and monthly_type == "last_day":
            # 月末は日次タスク + ランナースクリプトで対応
            runner_path = self._create_runner_script(task_name, day_spec, monthly_type, command)
            runner_command = f'python "{runner_path}"' if sys.platform == "win32" else f'python3 "{runner_path}"'
            self._scheduler.add(task_name, runner_command, "daily", time_spec)
        else:
            self._scheduler.add(
                task_name, command, frequency, time_spec,
                weekday=weekday, day_spec=day_spec
            )

    def _create_runner_script(
        self, task_name: str, day_spec: str, monthly_type: str, command: str
    ) -> str:
        """月末用ランナースクリプトを作成"""
        from frameworks.templates import load_template, render_template

        runners_dir = self._storage.get_runners_dir()
        runner_path = os.path.join(runners_dir, f"{task_name}.py")

        # 月末判定コード
        pattern = MonthlyPattern.parse(day_spec)
        condition_code = pattern.generate_condition_code()

        template = load_template("monthly_runner.py.template")
        script_content = render_template(
            template,
            task_name=task_name,
            condition_code=condition_code,
            command=command.replace("\\", "\\\\").replace('"', '\\"')
        )

        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        return runner_path

    def _remove_runner_script(self, name: str) -> None:
        """ランナースクリプトを削除"""
        runners_dir = self._storage.get_runners_dir()
        runner_path = os.path.join(runners_dir, f"{name}.py")
        if os.path.exists(runner_path):
            os.remove(runner_path)

    def _save_schedule_entry(
        self,
        task_name: str,
        frequency: str,
        time_spec: str,
        weekday: str,
        theme: str,
        context_file: str,
        file_list: str,
        lang: str,
        day_spec: str,
        monthly_type: str
    ) -> None:
        """スケジュールエントリをJSONに保存"""
        schedules = self._storage.load_schedules()

        # 同名のエントリを削除
        schedules = [s for s in schedules if s.get("name") != task_name]

        entry = {
            "name": task_name,
            "frequency": frequency,
            "weekday": weekday if frequency == "weekly" else "",
            "time": time_spec,
            "theme": theme,
            "context": context_file,
            "file_list": file_list,
            "lang": lang,
            "created": datetime.now().isoformat()
        }

        if frequency == "monthly":
            entry["day_spec"] = day_spec
            entry["monthly_type"] = monthly_type

        schedules.append(entry)
        self._storage.save_schedules(schedules)

    def _print_confirmation(
        self,
        task_name: str,
        frequency: str,
        time_spec: str,
        weekday: str,
        theme: str,
        context_file: str,
        file_list: str,
        lang: str,
        day_spec: str
    ) -> None:
        """確認メッセージを表示"""
        print(f"Schedule created: {task_name}")
        if frequency == "monthly":
            print(f"  Frequency: {frequency} ({day_spec})")
        elif frequency == "weekly":
            print(f"  Frequency: {frequency} ({weekday})")
        else:
            print(f"  Frequency: {frequency}")
        print(f"  Time: {time_spec}")
        if theme:
            print(f"  Theme: {theme}")
        if context_file:
            print(f"  Context: {context_file}")
        if file_list:
            print(f"  File list: {file_list}")
        if lang:
            print(f"  Language: {lang}")
        print()
        print("The essay will run automatically. Survives PC restart.")


# 便利関数（後方互換性用、main.pyから直接呼び出せるように）
def schedule_add(
    frequency: str,
    time_spec: str,
    weekday: str = "",
    theme: str = "",
    context_file: str = "",
    file_list: str = "",
    lang: str = "",
    name: str = "",
    day_spec: str = ""
) -> None:
    """スケジュールを追加する（便利関数）"""
    from adapters.scheduler import get_scheduler
    from adapters.storage import JsonStorageAdapter

    usecase = ScheduleEssayUseCase(get_scheduler(), JsonStorageAdapter())
    usecase.add(
        frequency=frequency,
        time_spec=time_spec,
        weekday=weekday,
        theme=theme,
        context_file=context_file,
        file_list=file_list,
        lang=lang,
        name=name,
        day_spec=day_spec
    )


def schedule_list() -> None:
    """スケジュール一覧を表示する（便利関数）"""
    from adapters.scheduler import get_scheduler
    from adapters.storage import JsonStorageAdapter

    usecase = ScheduleEssayUseCase(get_scheduler(), JsonStorageAdapter())
    usecase.list()


def schedule_remove(name: str) -> None:
    """スケジュールを削除する（便利関数）"""
    from adapters.scheduler import get_scheduler
    from adapters.storage import JsonStorageAdapter

    usecase = ScheduleEssayUseCase(get_scheduler(), JsonStorageAdapter())
    usecase.remove(name)
