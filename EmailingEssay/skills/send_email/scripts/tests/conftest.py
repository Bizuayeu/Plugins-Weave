# tests/conftest.py
"""
EmailingEssay テスト用共通 fixtures

Clean Architecture に基づき、各層のモックを提供する。
"""
import pytest
from unittest.mock import Mock
from typing import Protocol


# =============================================================================
# Port Protocols (Use Cases層の抽象インターフェース)
# =============================================================================

class MailPort(Protocol):
    """メール送信の抽象インターフェース"""
    def send(self, to: str, subject: str, body: str) -> None: ...
    def test(self) -> None: ...


class SchedulerPort(Protocol):
    """スケジューラの抽象インターフェース"""
    def add(self, task_name: str, command: str, frequency: str, **kwargs) -> None: ...
    def remove(self, name: str) -> None: ...
    def list(self) -> list: ...


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_mail_port():
    """MailPortのモック"""
    return Mock(spec=MailPort)


@pytest.fixture
def mock_scheduler_port():
    """SchedulerPortのモック"""
    return Mock(spec=SchedulerPort)


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
        "created": "2025-01-01T00:00:00"
    }
