# usecases/schedule_essay.py
"""
スケジュールエッセイユースケース

定期的なエッセイ配信のスケジュール管理を行う。
"""

from __future__ import annotations

import contextlib
import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from domain.code_generator import SafeCodeGenerator
from domain.models import MonthlyPattern, ScheduleConfig
from frameworks.logging_config import get_logger

from .command_builder import build_claude_command

if TYPE_CHECKING:
    from .ports import PathResolverPort, ScheduleEntry, SchedulerPort, ScheduleStoragePort

logger = get_logger("schedule")


class ScheduleEssayUseCase:
    """スケジュール管理ユースケース"""

    def __init__(
        self,
        scheduler_port: SchedulerPort,
        schedule_storage: ScheduleStoragePort,
        path_resolver: PathResolverPort,
    ) -> None:
        """
        Args:
            scheduler_port: SchedulerPort実装
            schedule_storage: ScheduleStoragePort実装
            path_resolver: PathResolverPort実装
        """
        self._scheduler = scheduler_port
        self._schedule_storage = schedule_storage
        self._path_resolver = path_resolver

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
        day_spec: str = "",
    ) -> None:
        """
        スケジュールを追加する（後方互換性維持のためのラッパー）。

        内部でScheduleConfigを作成してadd_from_config()に委譲する。

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
        config = ScheduleConfig(
            frequency=frequency,
            time_spec=time_spec,
            weekday=weekday,
            theme=theme,
            context_file=context_file,
            file_list=file_list,
            lang=lang,
            name=name,
            day_spec=day_spec,
        )
        self.add_from_config(config)

    def add_from_config(self, config: ScheduleConfig) -> None:
        """
        ScheduleConfigを使用してスケジュールを追加する。

        トランザクション的に動作し、途中で失敗した場合はロールバックする。

        Args:
            config: スケジュール設定を含むScheduleConfig

        Stage 1: パラメータ蓄積問題の解消
        """
        # バリデーション（Stage 3: ドメイン層に移行）
        config.validate()
        monthly_type = config.monthly_type

        # タスク名生成
        task_name = self._generate_task_name(
            config.frequency, config.time_spec, config.theme, config.name, config.day_spec
        )
        command = build_claude_command(
            config.theme, config.context_file, config.file_list, config.lang
        )

        # トランザクション的に実行
        scheduler_registered = False

        try:
            # Step 1: OSスケジューラに登録
            self._create_os_schedule(
                task_name,
                command,
                config.frequency,
                config.time_spec,
                weekday=config.weekday,
                day_spec=config.day_spec,
                monthly_type=monthly_type,
            )
            scheduler_registered = True

            # Step 2: JSONバックアップに保存（Stage 4: EssayScheduleを使用）
            from domain.models import EssaySchedule

            essay_schedule = EssaySchedule(
                name=task_name,
                frequency=config.frequency,
                time=config.time_spec,
                weekday=config.weekday if config.frequency == "weekly" else "",
                theme=config.theme,
                context=config.context_file,
                file_list=config.file_list,
                lang=config.lang,
                day_spec=config.day_spec if config.frequency == "monthly" else "",
                monthly_type=monthly_type if config.frequency == "monthly" else "",
            )
            self._save_schedule_entry(essay_schedule)

            # Step 3: 確認メッセージ
            self._print_confirmation(
                task_name,
                config.frequency,
                config.time_spec,
                config.weekday,
                config.theme,
                config.context_file,
                config.file_list,
                config.lang,
                config.day_spec,
            )

        except Exception:
            # ロールバック：スケジューラ登録を取り消す（失敗は無視、元の例外を優先）
            if scheduler_registered:
                with contextlib.suppress(Exception):
                    self._scheduler.remove(task_name)
            raise

    def list(self) -> None:
        """登録済みスケジュールを一覧表示する。"""
        # OSスケジューラから取得
        os_tasks = self._scheduler.list()
        os_task_names = {t["name"] for t in os_tasks}

        # JSONバックアップから取得
        schedules = self._schedule_storage.load_schedules()

        if not schedules and not os_tasks:
            logger.info("No schedules found.")
            return

        logger.info("Registered schedules:")
        logger.info("-" * 60)

        for sched in schedules:
            status = "active" if sched["name"] in os_task_names else "orphaned"
            freq_str = sched["frequency"]
            if sched.get("day_spec"):
                freq_str += f" ({sched['day_spec']})"
            elif sched.get("weekday"):
                freq_str += f" ({sched['weekday']})"

            logger.info(f"  {sched['name']}")
            logger.info(f"    Frequency: {freq_str} at {sched['time']}")
            if sched.get("theme"):
                logger.info(f"    Theme: {sched['theme']}")
            if sched.get("context"):
                logger.info(f"    Context: {sched['context']}")
            if sched.get("lang"):
                logger.info(f"    Language: {sched['lang']}")
            logger.info(f"    Status: {status}")
            logger.info("")

        # OS側のみにあるタスク
        json_names = {s["name"] for s in schedules}
        os_only = [t["name"] for t in os_tasks if t["name"] not in json_names]
        if os_only:
            logger.info("OS-only tasks (not in backup):")
            for t in os_only:
                logger.info(f"  {t}")

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
        schedules = self._schedule_storage.load_schedules()
        original_count = len(schedules)
        schedules = [s for s in schedules if s.get("name") != name]

        if len(schedules) < original_count:
            self._schedule_storage.save_schedules(schedules)
            logger.info(f"Removed schedule: {name}")
        else:
            logger.info(f"Schedule not found in backup: {name}")

    # Private methods
    # Note: Validation methods moved to ScheduleConfig.validate() (Stage 3)

    def _generate_task_name(
        self, frequency: str, time_spec: str, theme: str, name: str, day_spec: str
    ) -> str:
        """
        タスク名を生成する。

        明示的に名前が指定された場合はそのまま使用（既存動作：上書き可能）。
        自動生成の場合、既存タスクとの衝突を検出したらタイムスタンプ接尾辞を付与。
        """
        # 明示的な名前指定の場合はそのまま使用（上書き許可）
        if name:
            return name

        # 自動生成
        if frequency == "monthly" and day_spec:
            base = theme if theme else f"{frequency}_{day_spec}_{time_spec.replace(':', '')}"
        else:
            base = theme if theme else f"{frequency}_{time_spec.replace(':', '')}"
        safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in base)
        base_name = f"Essay_{safe_name}"

        # 既存タスク名との衝突チェック（自動生成名のみ）
        existing_names = {s["name"] for s in self._schedule_storage.load_schedules()}
        if base_name in existing_names:
            # タイムスタンプ接尾辞を付与してユニーク化
            suffix = datetime.now().strftime("%Y%m%d%H%M%S")
            base_name = f"{base_name}_{suffix}"
            logger.info(f"Task name collision detected, using unique name: {base_name}")

        return base_name

    def _create_os_schedule(
        self,
        task_name: str,
        command: str,
        frequency: str,
        time_spec: str,
        weekday: str = "",
        day_spec: str = "",
        monthly_type: str = "",
    ) -> None:
        """OSスケジューラにタスクを登録"""
        if frequency == "monthly" and monthly_type == "last_day":
            # 月末は日次タスク + ランナースクリプトで対応
            runner_path = self._create_runner_script(task_name, day_spec, monthly_type, command)
            runner_command = (
                f'python "{runner_path}"' if sys.platform == "win32" else f'python3 "{runner_path}"'
            )
            self._scheduler.add(task_name, runner_command, "daily", time_spec)
        else:
            self._scheduler.add(
                task_name, command, frequency, time_spec, weekday=weekday, day_spec=day_spec
            )

    def _create_runner_script(
        self, task_name: str, day_spec: str, monthly_type: str, command: str
    ) -> str:
        """月末用ランナースクリプトを作成"""
        from frameworks.templates import load_template, render_template

        runners_dir = Path(self._path_resolver.get_runners_dir())
        runner_path = runners_dir / f"{task_name}.py"

        # 月末判定コード
        pattern = MonthlyPattern.parse(day_spec)
        condition_code = pattern.generate_condition_code()

        template = load_template("monthly_runner.py.template")
        script_content = render_template(
            template,
            task_name=task_name,
            condition_code=condition_code,
            command=SafeCodeGenerator.escape_for_python_string(command),
        )

        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        return str(runner_path)

    def _remove_runner_script(self, name: str) -> None:
        """ランナースクリプトを削除"""
        runners_dir = Path(self._path_resolver.get_runners_dir())
        runner_path = runners_dir / f"{name}.py"
        if runner_path.exists():
            runner_path.unlink()

    def _save_schedule_entry(self, schedule: "EssaySchedule") -> None:
        """
        EssayScheduleをストレージに保存する。

        Stage 4: パラメータ集約によるメソッド簡略化

        Args:
            schedule: 保存するEssayScheduleオブジェクト
        """
        from domain.models import EssaySchedule

        schedules = self._schedule_storage.load_schedules()

        # 同名のエントリを削除
        schedules = [s for s in schedules if s.get("name") != schedule.name]

        # EssaySchedule.to_dict()を使用してエントリを作成
        entry = schedule.to_dict()

        # createdが空の場合は現在時刻をセット
        if not entry.get("created"):
            entry["created"] = datetime.now().isoformat()

        schedules.append(entry)
        self._schedule_storage.save_schedules(schedules)

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
        day_spec: str,
    ) -> None:
        """確認メッセージをログ出力"""
        logger.info(f"Schedule created: {task_name}")
        if frequency == "monthly":
            logger.info(f"  Frequency: {frequency} ({day_spec})")
        elif frequency == "weekly":
            logger.info(f"  Frequency: {frequency} ({weekday})")
        else:
            logger.info(f"  Frequency: {frequency}")
        logger.info(f"  Time: {time_spec}")
        if theme:
            logger.info(f"  Theme: {theme}")
        if context_file:
            logger.info(f"  Context: {context_file}")
        if file_list:
            logger.info(f"  File list: {file_list}")
        if lang:
            logger.info(f"  Language: {lang}")
        logger.info("")
        logger.info("The essay will run automatically. Survives PC restart.")
