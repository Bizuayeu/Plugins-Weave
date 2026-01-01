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
    def mock_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = []
        storage.get_runners_dir.return_value = "/tmp/runners"
        return storage

    @pytest.fixture
    def usecase(self, mock_scheduler, mock_storage):
        return ScheduleEssayUseCase(mock_scheduler, mock_storage)

    def test_add_daily_schedule(self, usecase, mock_scheduler, mock_storage):
        """日次スケジュールを追加できる"""
        usecase.add(frequency="daily", time_spec="09:00", theme="daily test")
        mock_scheduler.add.assert_called_once()
        mock_storage.save_schedules.assert_called_once()

    def test_add_weekly_schedule(self, usecase, mock_scheduler, mock_storage):
        """週次スケジュールを追加できる"""
        usecase.add(frequency="weekly", time_spec="10:00", weekday="monday", theme="weekly test")
        mock_scheduler.add.assert_called_once()

    def test_add_monthly_schedule(self, usecase, mock_scheduler, mock_storage):
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
    def mock_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = [
            {"name": "Essay_test", "frequency": "daily", "time": "09:00"}
        ]
        return storage

    def test_list_shows_schedules(self, mock_scheduler, mock_storage, capsys):
        """スケジュール一覧を表示"""
        usecase = ScheduleEssayUseCase(mock_scheduler, mock_storage)
        usecase.list()
        captured = capsys.readouterr()
        assert "Essay_test" in captured.out

    def test_list_shows_empty_message(self, capsys):
        """スケジュールなしでメッセージ表示"""
        scheduler = Mock()
        scheduler.list.return_value = []
        storage = Mock()
        storage.load_schedules.return_value = []

        usecase = ScheduleEssayUseCase(scheduler, storage)
        usecase.list()
        captured = capsys.readouterr()
        assert "No schedules" in captured.out or "スケジュール" in captured.out


class TestScheduleEssayUseCaseRemove:
    """remove() メソッドのテスト"""

    @pytest.fixture
    def mock_scheduler(self):
        return Mock()

    @pytest.fixture
    def mock_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = [
            {"name": "Essay_test", "frequency": "daily", "time": "09:00"}
        ]
        storage.get_runners_dir.return_value = "/tmp/runners"
        return storage

    def test_remove_existing_schedule(self, mock_scheduler, mock_storage, capsys):
        """既存スケジュールを削除"""
        usecase = ScheduleEssayUseCase(mock_scheduler, mock_storage)
        usecase.remove("Essay_test")
        mock_scheduler.remove.assert_called_once_with("Essay_test")
        mock_storage.save_schedules.assert_called_once()
        captured = capsys.readouterr()
        assert "Removed" in captured.out or "削除" in captured.out

    def test_remove_nonexistent_schedule(self, mock_scheduler, capsys):
        """存在しないスケジュールでメッセージ"""
        storage = Mock()
        storage.load_schedules.return_value = []
        storage.get_runners_dir.return_value = "/tmp/runners"

        usecase = ScheduleEssayUseCase(mock_scheduler, storage)
        usecase.remove("nonexistent")
        captured = capsys.readouterr()
        assert "not found" in captured.out or "見つかりません" in captured.out


class TestScheduleEssayUseCaseRollback:
    """add()メソッドのロールバック処理テスト（Item 2）"""

    @pytest.fixture
    def mock_scheduler(self):
        return Mock()

    @pytest.fixture
    def mock_storage(self):
        storage = Mock()
        storage.load_schedules.return_value = []
        storage.get_runners_dir.return_value = "/tmp/runners"
        return storage

    def test_rollback_scheduler_when_storage_fails(self, mock_scheduler, mock_storage):
        """ストレージ保存失敗時にスケジューラ登録をロールバック"""
        # ストレージ保存を失敗させる
        mock_storage.save_schedules.side_effect = PermissionError("Cannot write")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_storage)

        with pytest.raises(PermissionError):
            usecase.add(frequency="daily", time_spec="09:00", theme="test")

        # スケジューラに追加された後、ロールバックで削除される
        mock_scheduler.add.assert_called_once()
        mock_scheduler.remove.assert_called_once()

    def test_no_orphan_scheduler_entry_on_storage_failure(self, mock_scheduler, mock_storage):
        """ストレージ失敗時にスケジューラに孤児エントリが残らない"""
        mock_storage.save_schedules.side_effect = IOError("Disk full")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_storage)

        with pytest.raises(IOError):
            usecase.add(frequency="daily", time_spec="10:00", theme="orphan_test")

        # スケジューラのremoveが呼ばれたことを確認
        assert mock_scheduler.remove.called

    def test_scheduler_failure_does_not_save_to_storage(self, mock_scheduler, mock_storage):
        """スケジューラ登録失敗時はストレージに保存しない"""
        mock_scheduler.add.side_effect = RuntimeError("Scheduler unavailable")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_storage)

        with pytest.raises(RuntimeError):
            usecase.add(frequency="daily", time_spec="11:00", theme="scheduler_fail")

        # ストレージ保存は呼ばれない
        mock_storage.save_schedules.assert_not_called()

    def test_rollback_continues_even_if_remove_fails(self, mock_scheduler, mock_storage):
        """ロールバック中のremove失敗でも例外は元のまま"""
        mock_storage.save_schedules.side_effect = PermissionError("Cannot write")
        mock_scheduler.remove.side_effect = RuntimeError("Remove also failed")

        usecase = ScheduleEssayUseCase(mock_scheduler, mock_storage)

        # 元の例外（PermissionError）が発生する
        with pytest.raises(PermissionError):
            usecase.add(frequency="daily", time_spec="12:00", theme="double_fail")
