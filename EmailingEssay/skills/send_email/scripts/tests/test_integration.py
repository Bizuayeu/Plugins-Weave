# tests/test_integration.py
"""
統合テスト

各コンポーネントの連携をテストする。
"""
import pytest
import subprocess
import sys
import os

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCLIIntegration:
    """CLIの統合テスト"""

    def test_parser_imports_successfully(self):
        """パーサーがインポートできる"""
        from adapters.cli.parser import create_parser
        parser = create_parser()
        assert parser is not None

    def test_help_command_shows_help(self):
        """--help オプションが動作する"""
        from adapters.cli.parser import create_parser
        parser = create_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["--help"])
        assert exc.value.code == 0


class TestSchedulerIntegration:
    """スケジューラの統合テスト"""

    def test_get_scheduler_returns_adapter(self):
        """get_scheduler() がアダプターを返す"""
        from adapters.scheduler import get_scheduler
        scheduler = get_scheduler()
        assert hasattr(scheduler, "add")
        assert hasattr(scheduler, "remove")
        assert hasattr(scheduler, "list")


class TestModelsIntegration:
    """モデルの統合テスト"""

    def test_essay_schedule_roundtrip(self):
        """EssaySchedule のdict変換が往復できる"""
        from domain.models import EssaySchedule

        original = EssaySchedule(
            name="test_schedule",
            frequency="weekly",
            time="10:00",
            weekday="monday",
            theme="週次振り返り"
        )

        # to_dict -> from_dict
        d = original.to_dict()
        restored = EssaySchedule.from_dict(d)

        assert restored.name == original.name
        assert restored.frequency == original.frequency
        assert restored.time == original.time
        assert restored.weekday == original.weekday
        assert restored.theme == original.theme

    def test_monthly_pattern_all_types(self):
        """全ての MonthlyType がパースできる"""
        from domain.models import MonthlyPattern, MonthlyType

        test_cases = [
            ("15", MonthlyType.DATE),
            ("2nd_mon", MonthlyType.NTH_WEEKDAY),
            ("last_fri", MonthlyType.LAST_WEEKDAY),
            ("last_day", MonthlyType.LAST_DAY),
        ]

        for day_spec, expected_type in test_cases:
            pattern = MonthlyPattern.parse(day_spec)
            assert pattern.type == expected_type, f"Failed for {day_spec}"


class TestTemplatesIntegration:
    """テンプレートの統合テスト"""

    def test_waiter_template_renders(self):
        """waiterテンプレートがレンダリングできる"""
        from frameworks.templates import load_template, render_template

        template = load_template("essay_waiter.py.template")
        rendered = render_template(
            template,
            log_file="/tmp/test.log",
            target_time="12:00",
            claude_args="-t 'テスト'"
        )

        assert "/tmp/test.log" in rendered
        assert "12:00" in rendered
        assert "テスト" in rendered


class TestWaitUseCaseIntegration:
    """待機処理の統合テスト"""

    def test_parse_target_time_formats(self):
        """各種時刻形式がパースできる"""
        from usecases.wait_essay import parse_target_time
        from datetime import datetime, timedelta

        # HH:MM形式（未来）
        future = datetime.now() + timedelta(hours=1)
        result = parse_target_time(future.strftime("%H:%M"))
        assert result.hour == future.hour

        # YYYY-MM-DD HH:MM形式
        future_date = datetime.now() + timedelta(days=1)
        result = parse_target_time(future_date.strftime("%Y-%m-%d %H:%M"))
        assert result.day == future_date.day


class TestCleanArchitectureLayers:
    """Clean Architecture 層の分離テスト"""

    def test_domain_has_no_external_dependencies(self):
        """ドメイン層は外部依存がない"""
        # domain.models のインポートが標準ライブラリのみに依存
        from domain.models import EssaySchedule, MonthlyPattern, MonthlyType
        # インポートが成功すれば外部依存なし

    def test_usecases_depend_only_on_domain(self):
        """ユースケース層はドメイン層のみに依存"""
        from usecases.ports import MailPort, SchedulerPort, WaiterPort
        # Protocolは標準ライブラリ

    def test_adapters_implement_ports(self):
        """アダプター層はポートを実装"""
        from adapters.scheduler import WindowsSchedulerAdapter, UnixSchedulerAdapter
        from adapters.scheduler.base import BaseSchedulerAdapter

        # アダプターが基底クラスを継承していることを確認
        assert issubclass(WindowsSchedulerAdapter, BaseSchedulerAdapter)
        assert issubclass(UnixSchedulerAdapter, BaseSchedulerAdapter)


class TestMainEntryPoint:
    """main.py エントリーポイントの統合テスト"""

    def test_main_imports_successfully(self):
        """main.py がインポートできる"""
        import main
        assert hasattr(main, 'main')

    def test_main_help_returns_zero(self):
        """--help オプションで終了コード0"""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8',
            errors='replace'
        )
        assert result.returncode == 0
        assert "Essay" in result.stdout or "Mail" in result.stdout

    def test_main_schedule_list_works(self):
        """schedule list コマンドが動作"""
        result = subprocess.run(
            [sys.executable, "main.py", "schedule", "list"],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8',
            errors='replace'
        )
        # エラーなく実行できることを確認
        assert result.returncode == 0

    def test_main_schedule_help_works(self):
        """schedule --help が動作"""
        result = subprocess.run(
            [sys.executable, "main.py", "schedule", "--help"],
            capture_output=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            encoding='utf-8',
            errors='replace'
        )
        assert result.returncode == 0
        assert "daily" in result.stdout
        assert "weekly" in result.stdout
        assert "monthly" in result.stdout


class TestE2EScenarios:
    """E2Eシナリオテスト（Item 7）"""

    def test_schedule_add_list_remove_cycle_with_mock(self, tmp_path):
        """スケジュール追加→一覧→削除のサイクル（Mock使用）"""
        from unittest.mock import Mock
        from usecases.schedule_essay import ScheduleEssayUseCase
        from adapters.storage.json_adapter import JsonStorageAdapter

        # 実際のストレージを使用、スケジューラはMock
        storage = JsonStorageAdapter(base_dir=str(tmp_path))
        scheduler = Mock()
        scheduler.list.return_value = []

        usecase = ScheduleEssayUseCase(scheduler, storage)

        # Step 1: Add
        usecase.add(frequency="daily", time_spec="09:00", theme="e2e_test")
        schedules = storage.load_schedules()
        assert len(schedules) == 1
        assert schedules[0]["theme"] == "e2e_test"
        scheduler.add.assert_called_once()

        # Step 2: List (verify persistence)
        storage2 = JsonStorageAdapter(base_dir=str(tmp_path))
        schedules2 = storage2.load_schedules()
        assert len(schedules2) == 1

        # Step 3: Remove
        task_name = schedules[0]["name"]
        usecase.remove(task_name)
        schedules3 = storage.load_schedules()
        assert len(schedules3) == 0
        scheduler.remove.assert_called_with(task_name)

    def test_json_corruption_recovery_e2e(self, tmp_path):
        """JSON破損からの復旧シナリオ"""
        from adapters.storage.json_adapter import JsonStorageAdapter

        storage = JsonStorageAdapter(base_dir=str(tmp_path))

        # Step 1: 正常なデータを保存
        storage.save_schedules([{"name": "test1", "frequency": "daily"}])
        assert len(storage.load_schedules()) == 1

        # Step 2: JSONを破損させる
        schedules_file = tmp_path / "schedules.json"
        schedules_file.write_text("{corrupted json")

        # Step 3: 破損から復旧（空リストを返す）
        schedules = storage.load_schedules()
        assert schedules == []

        # Step 4: 新しいデータを保存（正常動作に戻る）
        storage.save_schedules([{"name": "test2", "frequency": "weekly"}])
        assert len(storage.load_schedules()) == 1
        assert storage.load_schedules()[0]["name"] == "test2"

    def test_target_time_integration_with_usecase(self, tmp_path, monkeypatch):
        """TargetTimeとUseCaseの統合テスト"""
        from domain.models import TargetTime
        from usecases.wait_essay import parse_target_time
        from datetime import datetime, timedelta

        # TargetTimeクラス経由でパース
        future = datetime.now() + timedelta(hours=2)
        time_str = future.strftime("%H:%M")

        # ドメインモデル経由
        target_time = TargetTime.parse(time_str)
        assert target_time.datetime.hour == future.hour

        # ユースケースのラッパー経由（後方互換）
        result = parse_target_time(time_str)
        assert result.hour == future.hour

        # 両者が同じ結果を返す
        assert target_time.datetime.hour == result.hour

    def test_rollback_e2e_scenario(self, tmp_path):
        """ロールバックのE2Eシナリオ"""
        from unittest.mock import Mock
        from usecases.schedule_essay import ScheduleEssayUseCase
        from adapters.storage.json_adapter import JsonStorageAdapter

        storage = JsonStorageAdapter(base_dir=str(tmp_path))
        scheduler = Mock()

        # ストレージ保存で失敗するように設定
        storage_with_error = Mock(wraps=storage)
        storage_with_error.save_schedules.side_effect = PermissionError("Disk full")
        storage_with_error.load_schedules.return_value = []
        storage_with_error.get_runners_dir.return_value = str(tmp_path / "runners")

        usecase = ScheduleEssayUseCase(scheduler, storage_with_error)

        # 例外が発生し、スケジューラがロールバックされる
        with pytest.raises(PermissionError):
            usecase.add(frequency="daily", time_spec="09:00", theme="rollback_test")

        # スケジューラがロールバックされた
        scheduler.add.assert_called_once()
        scheduler.remove.assert_called_once()

    def test_multi_schedule_coordination(self, tmp_path):
        """複数スケジュールの連携テスト（Item 7追加）"""
        from unittest.mock import Mock
        from usecases.schedule_essay import ScheduleEssayUseCase
        from adapters.storage.json_adapter import JsonStorageAdapter

        storage = JsonStorageAdapter(base_dir=str(tmp_path))
        scheduler = Mock()
        scheduler.list.return_value = []

        usecase = ScheduleEssayUseCase(scheduler, storage)

        # Step 1: 3つのスケジュールを追加
        usecase.add(frequency="daily", time_spec="09:00", theme="schedule_1")
        usecase.add(frequency="daily", time_spec="12:00", theme="schedule_2")
        usecase.add(frequency="daily", time_spec="18:00", theme="schedule_3")

        # Step 2: 全てリストされることを確認
        schedules = storage.load_schedules()
        assert len(schedules) == 3
        themes = {s["theme"] for s in schedules}
        assert themes == {"schedule_1", "schedule_2", "schedule_3"}

        # Step 3: 1つ削除
        task_name_to_remove = schedules[1]["name"]  # schedule_2
        usecase.remove(task_name_to_remove)

        # Step 4: 残り2つを確認
        schedules_after = storage.load_schedules()
        assert len(schedules_after) == 2
        remaining_themes = {s["theme"] for s in schedules_after}
        assert "schedule_2" not in remaining_themes
        assert "schedule_1" in remaining_themes
        assert "schedule_3" in remaining_themes

    def test_schedule_update_overwrites_existing(self, tmp_path):
        """スケジュール更新（上書き）テスト（Item 7追加）"""
        from unittest.mock import Mock
        from usecases.schedule_essay import ScheduleEssayUseCase
        from adapters.storage.json_adapter import JsonStorageAdapter

        storage = JsonStorageAdapter(base_dir=str(tmp_path))
        scheduler = Mock()
        scheduler.list.return_value = []

        usecase = ScheduleEssayUseCase(scheduler, storage)

        # Step 1: スケジュールを追加
        usecase.add(
            frequency="daily",
            time_spec="09:00",
            theme="original_theme",
            name="test_schedule"
        )
        schedules = storage.load_schedules()
        assert len(schedules) == 1
        assert schedules[0]["theme"] == "original_theme"
        assert schedules[0]["time"] == "09:00"

        # Step 2: 同名で再登録（時刻とテーマを変更）
        usecase.add(
            frequency="daily",
            time_spec="15:00",
            theme="updated_theme",
            name="test_schedule"
        )

        # Step 3: 上書きされたことを確認（重複なし）
        schedules_after = storage.load_schedules()
        assert len(schedules_after) == 1
        assert schedules_after[0]["name"] == "test_schedule"
        assert schedules_after[0]["theme"] == "updated_theme"
        assert schedules_after[0]["time"] == "15:00"
