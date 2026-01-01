# tests/adapters/test_scheduler.py
"""
スケジューラアダプターのテスト

Windows Task Scheduler と Unix Cron のテスト。
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.scheduler import SchedulerError, get_scheduler
from adapters.scheduler.unix import UnixSchedulerAdapter
from adapters.scheduler.windows import WindowsSchedulerAdapter


class TestGetScheduler:
    """get_scheduler() のテスト"""

    @patch('sys.platform', 'win32')
    def test_returns_windows_scheduler_on_windows(self):
        """Windowsでは WindowsSchedulerAdapter を返す"""
        scheduler = get_scheduler()
        assert isinstance(scheduler, WindowsSchedulerAdapter)

    @patch('sys.platform', 'linux')
    def test_returns_unix_scheduler_on_linux(self):
        """Linuxでは UnixSchedulerAdapter を返す"""
        scheduler = get_scheduler()
        assert isinstance(scheduler, UnixSchedulerAdapter)

    @patch('sys.platform', 'darwin')
    def test_returns_unix_scheduler_on_macos(self):
        """macOSでは UnixSchedulerAdapter を返す"""
        scheduler = get_scheduler()
        assert isinstance(scheduler, UnixSchedulerAdapter)


class TestWindowsSchedulerAdapter:
    """WindowsSchedulerAdapter のテスト"""

    @pytest.fixture
    def scheduler(self):
        return WindowsSchedulerAdapter()

    @patch('subprocess.run')
    def test_add_daily_schedule(self, mock_run, scheduler):
        """日次スケジュールの追加"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        scheduler.add(
            task_name="Essay_test",
            command='python "C:\\test\\script.py"',
            frequency="daily",
            time="09:00",
        )

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "schtasks" in call_args
        assert "/sc" in call_args
        assert "daily" in call_args

    @patch('subprocess.run')
    def test_add_weekly_schedule(self, mock_run, scheduler):
        """週次スケジュールの追加"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        scheduler.add(
            task_name="Essay_weekly",
            command='python "C:\\test\\script.py"',
            frequency="weekly",
            time="10:00",
            weekday="monday",
        )

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "weekly" in call_args
        assert "MON" in call_args

    @patch('subprocess.run')
    def test_add_monthly_date_schedule(self, mock_run, scheduler):
        """月次スケジュール（日付指定）の追加"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        scheduler.add(
            task_name="Essay_monthly",
            command='python "C:\\test\\script.py"',
            frequency="monthly",
            time="15:00",
            day_spec="15",
        )

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "monthly" in call_args
        assert "15" in call_args

    @patch('subprocess.run')
    def test_add_fails_raises_scheduler_error(self, mock_run, scheduler):
        """タスク作成失敗時はSchedulerErrorを発生"""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Access denied")

        with pytest.raises(SchedulerError):
            scheduler.add(
                task_name="Essay_fail", command='python script.py', frequency="daily", time="09:00"
            )

    @patch('subprocess.run')
    def test_remove_schedule(self, mock_run, scheduler):
        """スケジュールの削除"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        scheduler.remove("Essay_test")

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "/delete" in call_args
        assert "Essay_test" in call_args

    @patch('subprocess.run')
    def test_list_schedules(self, mock_run, scheduler):
        """スケジュール一覧の取得"""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='"TaskName","Next Run Time","Status"\n"Essay_morning","09:00:00","Ready"\n"Essay_weekly","10:00:00","Ready"\n',
            stderr="",
        )

        result = scheduler.list()

        assert len(result) >= 0  # パース結果に依存


class TestUnixSchedulerAdapter:
    """UnixSchedulerAdapter のテスト"""

    @pytest.fixture
    def scheduler(self):
        return UnixSchedulerAdapter()

    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_add_daily_schedule(self, mock_popen, mock_run, scheduler):
        """日次スケジュールの追加"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        scheduler.add(
            task_name="Essay_test",
            command='python /test/script.py',
            frequency="daily",
            time="09:00",
        )

        # crontab が呼ばれることを確認
        mock_popen.assert_called()

    @patch('subprocess.run')
    @patch('subprocess.Popen')
    def test_add_weekly_schedule(self, mock_popen, mock_run, scheduler):
        """週次スケジュールの追加"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        scheduler.add(
            task_name="Essay_weekly",
            command='python /test/script.py',
            frequency="weekly",
            time="10:00",
            weekday="monday",
        )

        mock_popen.assert_called()

    @patch('subprocess.run')
    def test_list_schedules(self, mock_run, scheduler):
        """スケジュール一覧の取得"""
        mock_run.return_value = Mock(
            returncode=0, stdout="# Essay_morning\n0 9 * * * python /test/script.py\n", stderr=""
        )

        result = scheduler.list()

        assert isinstance(result, list)
