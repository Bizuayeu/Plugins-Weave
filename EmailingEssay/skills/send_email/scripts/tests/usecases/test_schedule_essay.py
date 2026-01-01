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

    def test_list_shows_schedules(self, mock_scheduler, mock_schedule_storage, mock_path_resolver, capsys):
        """スケジュール一覧を表示"""
        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)
        usecase.list()
        captured = capsys.readouterr()
        assert "Essay_test" in captured.out

    def test_list_shows_empty_message(self, capsys):
        """スケジュールなしでメッセージ表示"""
        scheduler = Mock()
        scheduler.list.return_value = []
        schedule_storage = Mock()
        schedule_storage.load_schedules.return_value = []
        path_resolver = Mock()
        path_resolver.get_runners_dir.return_value = "/tmp/runners"

        usecase = ScheduleEssayUseCase(scheduler, schedule_storage, path_resolver)
        usecase.list()
        captured = capsys.readouterr()
        assert "No schedules" in captured.out or "スケジュール" in captured.out


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

    def test_remove_existing_schedule(self, mock_scheduler, mock_schedule_storage, mock_path_resolver, capsys):
        """既存スケジュールを削除"""
        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)
        usecase.remove("Essay_test")
        mock_scheduler.remove.assert_called_once_with("Essay_test")
        mock_schedule_storage.save_schedules.assert_called_once()
        captured = capsys.readouterr()
        assert "Removed" in captured.out or "削除" in captured.out

    def test_remove_nonexistent_schedule(self, mock_scheduler, mock_path_resolver, capsys):
        """存在しないスケジュールでメッセージ"""
        schedule_storage = Mock()
        schedule_storage.load_schedules.return_value = []

        usecase = ScheduleEssayUseCase(mock_scheduler, schedule_storage, mock_path_resolver)
        usecase.remove("nonexistent")
        captured = capsys.readouterr()
        assert "not found" in captured.out or "見つかりません" in captured.out


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

    def test_rollback_scheduler_when_storage_fails(self, mock_scheduler, mock_schedule_storage, mock_path_resolver):
        """ストレージ保存失敗時にスケジューラ登録をロールバック"""
        # ストレージ保存を失敗させる
        mock_schedule_storage.save_schedules.side_effect = PermissionError("Cannot write")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

        with pytest.raises(PermissionError):
            usecase.add(frequency="daily", time_spec="09:00", theme="test")

        # スケジューラに追加された後、ロールバックで削除される
        mock_scheduler.add.assert_called_once()
        mock_scheduler.remove.assert_called_once()

    def test_no_orphan_scheduler_entry_on_storage_failure(self, mock_scheduler, mock_schedule_storage, mock_path_resolver):
        """ストレージ失敗時にスケジューラに孤児エントリが残らない"""
        mock_schedule_storage.save_schedules.side_effect = OSError("Disk full")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

        with pytest.raises(IOError):
            usecase.add(frequency="daily", time_spec="10:00", theme="orphan_test")

        # スケジューラのremoveが呼ばれたことを確認
        assert mock_scheduler.remove.called

    def test_scheduler_failure_does_not_save_to_storage(self, mock_scheduler, mock_schedule_storage, mock_path_resolver):
        """スケジューラ登録失敗時はストレージに保存しない"""
        mock_scheduler.add.side_effect = RuntimeError("Scheduler unavailable")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

        with pytest.raises(RuntimeError):
            usecase.add(frequency="daily", time_spec="11:00", theme="scheduler_fail")

        # ストレージ保存は呼ばれない
        mock_schedule_storage.save_schedules.assert_not_called()

    def test_rollback_continues_even_if_remove_fails(self, mock_scheduler, mock_schedule_storage, mock_path_resolver):
        """ロールバック中のremove失敗でも例外は元のまま"""
        mock_schedule_storage.save_schedules.side_effect = PermissionError("Cannot write")
        mock_scheduler.remove.side_effect = RuntimeError("Remove also failed")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_schedule_storage, mock_path_resolver)

        # 元の例外（PermissionError）が発生する
        with pytest.raises(PermissionError):
            usecase.add(frequency="daily", time_spec="12:00", theme="double_fail")
