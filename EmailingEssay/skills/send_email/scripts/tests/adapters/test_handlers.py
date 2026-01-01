# tests/adapters/test_handlers.py
"""
CLI ハンドラのテスト

各コマンドハンドラが適切にUse Caseを呼び出すことを検証する。
"""
import pytest
import sys
import os
from argparse import Namespace
from unittest.mock import Mock, MagicMock

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.cli.handlers import (
    handle_test,
    handle_send,
    handle_wait,
    handle_schedule_list,
    handle_schedule_remove,
    handle_schedule_daily,
    handle_schedule_weekly,
    handle_schedule_monthly,
)


class TestHandleTest:
    """handle_test() のテスト"""

    def test_calls_mail_port_test(self):
        """MailPortのtest()を呼び出す"""
        mock_mail = Mock()
        args = Namespace()

        handle_test(args, mail_port=mock_mail)

        mock_mail.test.assert_called_once()


class TestHandleSend:
    """handle_send() のテスト"""

    def test_calls_mail_port_send(self):
        """MailPortのsend()を呼び出す"""
        mock_mail = Mock()
        args = Namespace(subject="Test Subject", body="Test Body")

        handle_send(args, mail_port=mock_mail)

        mock_mail.send.assert_called_once()


class TestHandleWait:
    """handle_wait() のテスト"""

    def test_calls_waiter_port_spawn(self):
        """WaiterPortのspawn()を呼び出す"""
        mock_waiter = Mock()
        args = Namespace(
            time="09:30",
            theme="test_theme",
            context="/path/to/context",
            file_list="",
            lang="ja"
        )

        handle_wait(args, waiter_port=mock_waiter)

        mock_waiter.spawn.assert_called_once_with(
            target_time="09:30",
            theme="test_theme",
            context="/path/to/context",
            file_list="",
            lang="ja"
        )


class TestHandleScheduleList:
    """handle_schedule_list() のテスト"""

    def test_calls_scheduler_port_list(self):
        """SchedulerPortのlist()を呼び出す"""
        mock_scheduler = Mock()
        mock_scheduler.list.return_value = []
        args = Namespace()

        handle_schedule_list(args, scheduler_port=mock_scheduler)

        mock_scheduler.list.assert_called_once()


class TestHandleScheduleRemove:
    """handle_schedule_remove() のテスト"""

    def test_calls_scheduler_port_remove(self):
        """SchedulerPortのremove()を呼び出す"""
        mock_scheduler = Mock()
        args = Namespace(name="task_to_remove")

        handle_schedule_remove(args, scheduler_port=mock_scheduler)

        mock_scheduler.remove.assert_called_once_with("task_to_remove")


class TestHandleScheduleDaily:
    """handle_schedule_daily() のテスト"""

    def test_calls_scheduler_port_add_with_daily(self):
        """SchedulerPortのadd()をdailyで呼び出す"""
        mock_scheduler = Mock()
        args = Namespace(
            time="09:00",
            theme="morning",
            context="",
            file_list="",
            lang="auto",
            name=""
        )

        handle_schedule_daily(args, scheduler_port=mock_scheduler)

        mock_scheduler.add.assert_called_once()
        call_kwargs = mock_scheduler.add.call_args
        # frequencyがdailyであることを確認
        assert call_kwargs[1]["frequency"] == "daily"
        assert call_kwargs[1]["time"] == "09:00"


class TestHandleScheduleWeekly:
    """handle_schedule_weekly() のテスト"""

    def test_calls_scheduler_port_add_with_weekly(self):
        """SchedulerPortのadd()をweeklyで呼び出す"""
        mock_scheduler = Mock()
        args = Namespace(
            weekday="monday",
            time="10:00",
            theme="",
            context="",
            file_list="",
            lang="auto",
            name=""
        )

        handle_schedule_weekly(args, scheduler_port=mock_scheduler)

        mock_scheduler.add.assert_called_once()
        call_kwargs = mock_scheduler.add.call_args
        assert call_kwargs[1]["frequency"] == "weekly"
        assert call_kwargs[1]["weekday"] == "monday"
        assert call_kwargs[1]["time"] == "10:00"


class TestHandleScheduleMonthly:
    """handle_schedule_monthly() のテスト"""

    def test_calls_scheduler_port_add_with_monthly(self):
        """SchedulerPortのadd()をmonthlyで呼び出す"""
        mock_scheduler = Mock()
        args = Namespace(
            day_spec="last_fri",
            time="15:00",
            theme="",
            context="",
            file_list="",
            lang="auto",
            name=""
        )

        handle_schedule_monthly(args, scheduler_port=mock_scheduler)

        mock_scheduler.add.assert_called_once()
        call_kwargs = mock_scheduler.add.call_args
        assert call_kwargs[1]["frequency"] == "monthly"
        assert call_kwargs[1]["day_spec"] == "last_fri"
        assert call_kwargs[1]["time"] == "15:00"
