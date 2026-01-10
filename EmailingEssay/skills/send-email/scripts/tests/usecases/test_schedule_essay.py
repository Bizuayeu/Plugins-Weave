# tests/usecases/test_schedule_essay.py
"""
ScheduleEssayUseCase のユニットテスト

Phase 9.1: TDD補完 - Phase 9で漏れたテストを追加
"""

import os
import sys
from unittest.mock import MagicMock, Mock

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from usecases.schedule_essay import ScheduleEssayUseCase


class TestScheduleEssayUseCaseAdd:
    """add() メソッドのテスト"""

    @pytest.fixture
    def mock_scheduler(self):
        return Mock()

    @pytest.fixture
    def mock_schedule_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = []
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        resolver = Mock()
        runners_dir = tmp_path / "runners"
        runners_dir.mkdir(exist_ok=True)
        resolver.get_runners_dir.return_value = str(runners_dir)
        return resolver

    @pytest.fixture
    def usecase(self, mock_scheduler, mock_schedule_storage, mock_path_resolver):
        return ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

    def test_add_daily_schedule(self, usecase, mock_scheduler, mock_schedule_storage):
        """日次スケジュールを追加できる"""
        usecase.add(frequency="daily", time_spec="09:00", theme="daily test")
        mock_scheduler.add.assert_called_once()
        mock_schedule_storage.save_schedules.assert_called_once()

    def test_add_weekly_schedule(self, usecase, mock_scheduler):
        """週次スケジュールを追加できる"""
        usecase.add(frequency="weekly", time_spec="10:00", weekday="monday", theme="weekly test")
        mock_scheduler.add.assert_called_once()

    def test_add_monthly_schedule(self, usecase, mock_scheduler):
        """月次スケジュールを追加できる"""
        usecase.add(frequency="monthly", time_spec="15:00", day_spec="15", theme="monthly test")
        mock_scheduler.add.assert_called_once()

    def test_add_invalid_frequency_raises_error(self, usecase):
        """無効な頻度でエラー"""
        with pytest.raises(ValueError, match="frequency must be"):
            usecase.add(frequency="hourly", time_spec="09:00")

    def test_add_invalid_time_format_raises_error(self, usecase):
        """無効な時刻形式でエラー"""
        with pytest.raises(ValueError, match="HH:MM format"):
            usecase.add(frequency="daily", time_spec="9:00:00")

    def test_add_weekly_without_weekday_raises_error(self, usecase):
        """週次で曜日なしはエラー"""
        with pytest.raises(ValueError, match="weekday"):
            usecase.add(frequency="weekly", time_spec="10:00", weekday="")

    def test_add_monthly_without_day_spec_raises_error(self, usecase):
        """月次でday_specなしはエラー"""
        with pytest.raises(ValueError, match="day_spec"):
            usecase.add(frequency="monthly", time_spec="10:00")


class TestScheduleEssayUseCaseList:
    """list() メソッドのテスト"""

    @pytest.fixture
    def mock_scheduler(self):
        scheduler = Mock()
        scheduler.list.return_value = [{"name": "Essay_test"}]
        return scheduler

    @pytest.fixture
    def mock_schedule_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = [
            {"name": "Essay_test", "frequency": "daily", "time": "09:00"}
        ]
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        resolver = Mock()
        resolver.get_runners_dir.return_value = str(tmp_path / "runners")
        return resolver

    def test_list_shows_schedules(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver, caplog
    ):
        """スケジュール一覧を表示"""
        import logging

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)
        with caplog.at_level(logging.INFO):
            usecase.list()
        assert any("Essay_test" in record.message for record in caplog.records)

    def test_list_shows_empty_message(self, caplog):
        """スケジュールなしでメッセージ表示"""
        import logging

        scheduler = Mock()
        scheduler.list.return_value = []
        schedule_storage = Mock()
        schedule_storage.load_schedules.return_value = []
        path_resolver = Mock()
        path_resolver.get_runners_dir.return_value = "/tmp/runners"

        usecase = ScheduleEssayUseCase(scheduler, schedule_storage, path_resolver)
        with caplog.at_level(logging.INFO):
            usecase.list()
        assert any("No schedules" in record.message for record in caplog.records)


class TestScheduleEssayUseCaseRemove:
    """remove() メソッドのテスト"""

    @pytest.fixture
    def mock_scheduler(self):
        return Mock()

    @pytest.fixture
    def mock_schedule_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = [
            {"name": "Essay_test", "frequency": "daily", "time": "09:00"}
        ]
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        resolver = Mock()
        resolver.get_runners_dir.return_value = str(tmp_path / "runners")
        return resolver

    def test_remove_existing_schedule(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver, caplog
    ):
        """既存スケジュールを削除"""
        import logging

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)
        with caplog.at_level(logging.INFO):
            usecase.remove("Essay_test")
        mock_scheduler.remove.assert_called_once_with("Essay_test")
        mock_schedule_storage.save_schedules.assert_called_once()
        assert any("Removed" in record.message for record in caplog.records)

    def test_remove_nonexistent_schedule(self, mock_scheduler, mock_path_resolver, caplog):
        """存在しないスケジュールでメッセージ"""
        import logging

        schedule_storage = Mock()
        schedule_storage.load_schedules.return_value = []

        usecase = ScheduleEssayUseCase(mock_scheduler, schedule_storage, mock_path_resolver)
        with caplog.at_level(logging.INFO):
            usecase.remove("nonexistent")
        assert any("not found" in record.message for record in caplog.records)


class TestScheduleEssayUseCaseSeparatedPorts:
    """分離Port使用のテスト（Phase C: StoragePort除去）"""

    @pytest.fixture
    def mock_scheduler(self):
        return Mock()

    @pytest.fixture
    def mock_schedule_storage(self):
        """ScheduleStoragePort用モック"""
        storage = Mock()
        storage.load_schedules.return_value = []
        storage.save_schedules.return_value = None
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        """PathResolverPort用モック"""
        resolver = Mock()
        runners_dir = tmp_path / "runners"
        runners_dir.mkdir(exist_ok=True)
        resolver.get_runners_dir.return_value = str(runners_dir)
        resolver.get_persistent_dir.return_value = str(tmp_path)
        return resolver

    def test_constructor_accepts_separated_ports(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """コンストラクタが分離されたポートを受け取る"""
        usecase = ScheduleEssayUseCase(
            scheduler_port=mock_scheduler,
            schedule_storage=mock_schedule_storage,
            path_resolver=mock_path_resolver,
        )
        assert usecase is not None

    def test_add_uses_schedule_storage(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """add()がScheduleStoragePortを使用する"""
        usecase = ScheduleEssayUseCase(
            scheduler_port=mock_scheduler,
            schedule_storage=mock_schedule_storage,
            path_resolver=mock_path_resolver,
        )
        usecase.add(frequency="daily", time_spec="09:00", theme="test")
        mock_schedule_storage.save_schedules.assert_called_once()

    def test_add_uses_path_resolver_for_runners(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """add()がPathResolverPortを使用（月次last_day時）"""
        usecase = ScheduleEssayUseCase(
            scheduler_port=mock_scheduler,
            schedule_storage=mock_schedule_storage,
            path_resolver=mock_path_resolver,
        )
        usecase.add(frequency="monthly", time_spec="15:00", day_spec="last_day", theme="test")
        mock_path_resolver.get_runners_dir.assert_called()

    def test_list_uses_schedule_storage(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """list()がScheduleStoragePortを使用する"""
        mock_schedule_storage.load_schedules.return_value = [
            {"name": "test", "frequency": "daily", "time": "09:00"}
        ]
        mock_scheduler.list.return_value = [{"name": "test"}]
        usecase = ScheduleEssayUseCase(
            scheduler_port=mock_scheduler,
            schedule_storage=mock_schedule_storage,
            path_resolver=mock_path_resolver,
        )
        usecase.list()
        mock_schedule_storage.load_schedules.assert_called()

    def test_remove_uses_path_resolver(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """remove()がPathResolverPortを使用する"""
        mock_schedule_storage.load_schedules.return_value = [
            {"name": "test", "frequency": "daily", "time": "09:00"}
        ]
        usecase = ScheduleEssayUseCase(
            scheduler_port=mock_scheduler,
            schedule_storage=mock_schedule_storage,
            path_resolver=mock_path_resolver,
        )
        usecase.remove("test")
        mock_path_resolver.get_runners_dir.assert_called()


class TestScheduleEssayUseCaseRollback:
    """add()メソッドのロールバック処理テスト（Item 2）"""

    @pytest.fixture
    def mock_scheduler(self):
        return Mock()

    @pytest.fixture
    def mock_schedule_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = []
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        resolver = Mock()
        runners_dir = tmp_path / "runners"
        runners_dir.mkdir(exist_ok=True)
        resolver.get_runners_dir.return_value = str(runners_dir)
        return resolver

    def test_rollback_scheduler_when_storage_fails(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """ストレージ保存失敗時にスケジューラ登録をロールバック"""
        # ストレージ保存を失敗させる
        mock_schedule_storage.save_schedules.side_effect = PermissionError("Cannot write")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

        with pytest.raises(PermissionError):
            usecase.add(frequency="daily", time_spec="09:00", theme="test")

        # スケジューラに追加された後、ロールバックで削除される
        mock_scheduler.add.assert_called_once()
        mock_scheduler.remove.assert_called_once()

    def test_no_orphan_scheduler_entry_on_storage_failure(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """ストレージ失敗時にスケジューラに孤児エントリが残らない"""
        mock_schedule_storage.save_schedules.side_effect = OSError("Disk full")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

        with pytest.raises(IOError):
            usecase.add(frequency="daily", time_spec="10:00", theme="orphan_test")

        # スケジューラのremoveが呼ばれたことを確認
        assert mock_scheduler.remove.called

    def test_scheduler_failure_does_not_save_to_storage(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """スケジューラ登録失敗時はストレージに保存しない"""
        mock_scheduler.add.side_effect = RuntimeError("Scheduler unavailable")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

        with pytest.raises(RuntimeError):
            usecase.add(frequency="daily", time_spec="11:00", theme="scheduler_fail")

        # ストレージ保存は呼ばれない
        mock_schedule_storage.save_schedules.assert_not_called()

    def test_rollback_continues_even_if_remove_fails(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver
    ):
        """ロールバック中のremove失敗でも例外は元のまま"""
        mock_schedule_storage.save_schedules.side_effect = PermissionError("Cannot write")
        mock_scheduler.remove.side_effect = RuntimeError("Remove also failed")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

        # 元の例外（PermissionError）が発生する
        with pytest.raises(PermissionError):
            usecase.add(frequency="daily", time_spec="12:00", theme="double_fail")


class TestScheduleEssayUseCaseWithConfig:
    """ScheduleConfigを使用したadd()メソッドのテスト（Stage 1: パラメータ蓄積問題の解消）"""

    @pytest.fixture
    def mock_scheduler(self):
        return Mock()

    @pytest.fixture
    def mock_schedule_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = []
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        resolver = Mock()
        runners_dir = tmp_path / "runners"
        runners_dir.mkdir(exist_ok=True)
        resolver.get_runners_dir.return_value = str(runners_dir)
        return resolver

    @pytest.fixture
    def usecase(self, mock_scheduler, mock_schedule_storage, mock_path_resolver):
        return ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

    def test_add_from_config_daily(self, usecase, mock_scheduler, mock_schedule_storage):
        """ScheduleConfigで日次スケジュールを追加"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="daily", time_spec="09:00", theme="daily config test")
        usecase.add_from_config(config)
        mock_scheduler.add.assert_called_once()
        mock_schedule_storage.save_schedules.assert_called_once()

    def test_add_from_config_weekly(self, usecase, mock_scheduler):
        """ScheduleConfigで週次スケジュールを追加"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(
            frequency="weekly", time_spec="10:00", weekday="monday", theme="weekly config test"
        )
        usecase.add_from_config(config)
        mock_scheduler.add.assert_called_once()

    def test_add_from_config_monthly(self, usecase, mock_scheduler):
        """ScheduleConfigで月次スケジュールを追加"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(
            frequency="monthly", time_spec="15:00", day_spec="15", theme="monthly config test"
        )
        usecase.add_from_config(config)
        mock_scheduler.add.assert_called_once()

    def test_add_from_config_with_all_options(self, usecase, mock_scheduler, mock_schedule_storage):
        """ScheduleConfigで全オプション指定"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(
            frequency="daily",
            time_spec="22:00",
            theme="全オプションテスト",
            context_file="/path/to/context.md",
            file_list="/path/to/files.txt",
            lang="ja",
            name="custom_task_name",
        )
        usecase.add_from_config(config)
        mock_scheduler.add.assert_called_once()
        mock_schedule_storage.save_schedules.assert_called_once()

    def test_add_from_config_invalid_frequency(self, usecase):
        """ScheduleConfigで無効な頻度はエラー"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="hourly", time_spec="09:00")
        with pytest.raises(ValueError, match="frequency must be"):
            usecase.add_from_config(config)

    def test_add_from_config_weekly_without_weekday(self, usecase):
        """ScheduleConfigで週次・曜日なしはエラー"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="weekly", time_spec="10:00")
        with pytest.raises(ValueError, match="weekday"):
            usecase.add_from_config(config)

    def test_add_from_config_monthly_without_day_spec(self, usecase):
        """ScheduleConfigで月次・day_specなしはエラー"""
        from domain.models import ScheduleConfig

        config = ScheduleConfig(frequency="monthly", time_spec="10:00")
        with pytest.raises(ValueError, match="day_spec"):
            usecase.add_from_config(config)


class TestScheduleEssayUseCaseLogging:
    """出力ログのテスト（Stage 2: print→logger）"""

    import logging

    @pytest.fixture
    def mock_scheduler(self):
        scheduler = Mock()
        scheduler.list.return_value = [{"name": "Essay_test"}]
        return scheduler

    @pytest.fixture
    def mock_schedule_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = [
            {"name": "Essay_test", "frequency": "daily", "time": "09:00"}
        ]
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        resolver = Mock()
        runners_dir = tmp_path / "runners"
        runners_dir.mkdir(exist_ok=True)
        resolver.get_runners_dir.return_value = str(runners_dir)
        return resolver

    @pytest.fixture
    def usecase(self, mock_scheduler, mock_schedule_storage, mock_path_resolver):
        return ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

    def test_list_logs_schedules(self, usecase, caplog):
        """list()がスケジュールをログ出力する"""
        import logging

        with caplog.at_level(logging.INFO):
            usecase.list()
        assert any("Essay_test" in record.message for record in caplog.records)

    def test_list_empty_logs_no_schedules(self, mock_scheduler, mock_path_resolver, caplog):
        """スケジュールなしでメッセージをログ出力"""
        import logging

        scheduler = Mock()
        scheduler.list.return_value = []
        schedule_storage = Mock()
        schedule_storage.load_schedules.return_value = []

        usecase = ScheduleEssayUseCase(scheduler, schedule_storage, mock_path_resolver)
        with caplog.at_level(logging.INFO):
            usecase.list()
        assert any("No schedules" in record.message for record in caplog.records)

    def test_remove_logs_success(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver, caplog
    ):
        """remove()が成功をログ出力"""
        import logging

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)
        with caplog.at_level(logging.INFO):
            usecase.remove("Essay_test")
        assert any("Removed" in record.message for record in caplog.records)

    def test_remove_nonexistent_logs_not_found(self, mock_scheduler, mock_path_resolver, caplog):
        """存在しないスケジュール削除でログ出力"""
        import logging

        schedule_storage = Mock()
        schedule_storage.load_schedules.return_value = []

        usecase = ScheduleEssayUseCase(mock_scheduler, schedule_storage, mock_path_resolver)
        with caplog.at_level(logging.INFO):
            usecase.remove("nonexistent")
        assert any("not found" in record.message for record in caplog.records)

    def test_add_logs_confirmation(
        self, mock_scheduler, mock_schedule_storage, mock_path_resolver, caplog
    ):
        """add()が確認メッセージをログ出力"""
        import logging

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)
        with caplog.at_level(logging.INFO):
            usecase.add(frequency="daily", time_spec="09:00", theme="test")
        assert any("Schedule created" in record.message for record in caplog.records)


class TestSaveScheduleEntry:
    """_save_schedule_entry のテスト（Stage 4: パラメータ集約）"""

    @pytest.fixture
    def mock_scheduler(self):
        return Mock()

    @pytest.fixture
    def mock_schedule_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = []
        return storage

    @pytest.fixture
    def mock_path_resolver(self, tmp_path):
        resolver = Mock()
        runners_dir = tmp_path / "runners"
        runners_dir.mkdir(exist_ok=True)
        resolver.get_runners_dir.return_value = str(runners_dir)
        return resolver

    @pytest.fixture
    def usecase(self, mock_scheduler, mock_schedule_storage, mock_path_resolver):
        return ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

    def test_saves_essay_schedule_to_storage(self, usecase, mock_schedule_storage):
        """EssaySchedule が正しく保存される"""
        from domain.models import EssaySchedule

        schedule = EssaySchedule(
            name="test_schedule",
            frequency="daily",
            time="22:00",
            theme="test theme",
        )
        usecase._save_schedule_entry(schedule)

        # save_schedules が呼ばれたことを確認
        mock_schedule_storage.save_schedules.assert_called_once()
        saved_data = mock_schedule_storage.save_schedules.call_args[0][0]
        assert len(saved_data) == 1
        assert saved_data[0]["name"] == "test_schedule"
        assert saved_data[0]["frequency"] == "daily"
        assert saved_data[0]["time"] == "22:00"
        assert saved_data[0]["theme"] == "test theme"

    def test_saves_weekly_essay_schedule(self, usecase, mock_schedule_storage):
        """週次EssayScheduleが正しく保存される"""
        from domain.models import EssaySchedule

        schedule = EssaySchedule(
            name="weekly_test",
            frequency="weekly",
            time="10:00",
            weekday="monday",
            theme="weekly theme",
        )
        usecase._save_schedule_entry(schedule)

        saved_data = mock_schedule_storage.save_schedules.call_args[0][0]
        assert saved_data[0]["weekday"] == "monday"

    def test_saves_monthly_essay_schedule(self, usecase, mock_schedule_storage):
        """月次EssayScheduleが正しく保存される"""
        from domain.models import EssaySchedule

        schedule = EssaySchedule(
            name="monthly_test",
            frequency="monthly",
            time="15:00",
            day_spec="15",
            monthly_type="date",
            theme="monthly theme",
        )
        usecase._save_schedule_entry(schedule)

        saved_data = mock_schedule_storage.save_schedules.call_args[0][0]
        assert saved_data[0]["day_spec"] == "15"
        assert saved_data[0]["monthly_type"] == "date"

    def test_overwrites_existing_schedule_with_same_name(self, usecase, mock_schedule_storage):
        """同名スケジュールを上書き"""
        from domain.models import EssaySchedule

        # 既存データをセット
        mock_schedule_storage.load_schedules.return_value = [
            {"name": "existing", "frequency": "daily", "time": "08:00"}
        ]

        schedule = EssaySchedule(
            name="existing",
            frequency="daily",
            time="22:00",
            theme="updated",
        )
        usecase._save_schedule_entry(schedule)

        saved_data = mock_schedule_storage.save_schedules.call_args[0][0]
        assert len(saved_data) == 1
        assert saved_data[0]["time"] == "22:00"
        assert saved_data[0]["theme"] == "updated"
