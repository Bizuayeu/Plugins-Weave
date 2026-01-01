# tests/usecases/test_schedule_essay.py
"""
ScheduleEssayUseCase のユニットテスト

Phase 9.1: TDD補完 - Phase 9で漏れたテストを追加
"""
import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

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
        usecase.add(
            frequency="daily",
            time_spec="09:00",
            theme="daily test"
        )
        mock_scheduler.add.assert_called_once()
        mock_storage.save_schedules.assert_called_once()

    def test_add_weekly_schedule(self, usecase, mock_scheduler, mock_storage):
        """週次スケジュールを追加できる"""
        usecase.add(
            frequency="weekly",
            time_spec="10:00",
            weekday="monday",
            theme="weekly test"
        )
        mock_scheduler.add.assert_called_once()

    def test_add_monthly_schedule(self, usecase, mock_scheduler, mock_storage):
        """月次スケジュールを追加できる"""
        usecase.add(
            frequency="monthly",
            time_spec="15:00",
            day_spec="15",
            theme="monthly test"
        )
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
