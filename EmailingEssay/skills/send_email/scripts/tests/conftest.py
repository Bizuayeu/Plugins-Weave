# tests/conftest.py
"""
EmailingEssay テスト用共通 fixtures

Clean Architecture に基づき、各層のモックを提供する。
本番のportsをインポートし、create_autospecで型安全なモックを生成。
"""

from unittest.mock import create_autospec

import pytest

# 本番のPortsをインポート（重複定義を排除）
from usecases.ports import (
    MailPort,
    ProcessSpawnerPort,
    SchedulerPort,
    ScheduleStoragePort,
    WaiterStoragePort,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_mail_port():
    """MailPortのモック（create_autospecで型安全）"""
    return create_autospec(MailPort, instance=True)


@pytest.fixture
def mock_scheduler_port():
    """SchedulerPortのモック"""
    return create_autospec(SchedulerPort, instance=True)


@pytest.fixture
def mock_schedule_storage():
    """ScheduleStoragePortのモック"""
    mock = create_autospec(ScheduleStoragePort, instance=True)
    mock.load_schedules.return_value = []
    return mock


@pytest.fixture
def mock_waiter_storage():
    """WaiterStoragePortのモック"""
    mock = create_autospec(WaiterStoragePort, instance=True)
    mock.get_active_waiters.return_value = []
    return mock


@pytest.fixture
def mock_process_spawner():
    """ProcessSpawnerPortのモック"""
    return create_autospec(ProcessSpawnerPort, instance=True)


@pytest.fixture
def sample_schedule_dict():
    """テスト用スケジュールデータ"""
    return {
        "name": "test_schedule",
        "frequency": "daily",
        "time": "09:00",
        "theme": "テスト",
        "context": "",
        "file_list": "",
        "lang": "ja",
        "created": "2025-01-01T00:00:00",
    }
