# tests/usecases/test_factories.py
"""
factories.py のテスト

ファクトリ関数のテスト。
Stage 5: Protocol準拠検証テストを追加。
"""

import os
import sys
from unittest.mock import Mock, patch

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from usecases.ports import (
    MailPort,
    PathResolverPort,
    ProcessSpawnerPort,
    SchedulerPort,
    ScheduleStoragePort,
    WaiterStoragePort,
)

# =============================================================================
# Stage 5: Protocol準拠テスト
# =============================================================================


class TestProtocolConformance:
    """アダプターがProtocolに準拠していることを検証するテスト"""

    def test_scheduler_conforms_to_protocol(self):
        """スケジューラアダプターがSchedulerPortに準拠する"""
        from adapters.scheduler import get_scheduler

        scheduler = get_scheduler()
        assert isinstance(scheduler, SchedulerPort)

    def test_storage_conforms_to_schedule_storage_protocol(self):
        """JsonStorageAdapterがScheduleStoragePortに準拠する"""
        from adapters.storage import JsonStorageAdapter

        storage = JsonStorageAdapter()
        assert isinstance(storage, ScheduleStoragePort)

    def test_storage_conforms_to_waiter_storage_protocol(self):
        """JsonStorageAdapterがWaiterStoragePortに準拠する"""
        from adapters.storage import JsonStorageAdapter

        storage = JsonStorageAdapter()
        assert isinstance(storage, WaiterStoragePort)

    def test_storage_conforms_to_path_resolver_protocol(self):
        """JsonStorageAdapterがPathResolverPortに準拠する"""
        from adapters.storage import JsonStorageAdapter

        storage = JsonStorageAdapter()
        assert isinstance(storage, PathResolverPort)

    def test_spawner_conforms_to_protocol(self):
        """ProcessSpawnerがProcessSpawnerPortに準拠する"""
        from adapters.process import ProcessSpawner

        spawner = ProcessSpawner()
        assert isinstance(spawner, ProcessSpawnerPort)

    def test_mail_adapter_conforms_to_protocol(self):
        """YagmailAdapterがMailPortに準拠する（設定不要でインスタンス化テスト）"""
        # YagmailAdapterは設定が必要なので、クラス定義レベルでチェック
        from adapters.mail import YagmailAdapter

        # メソッド存在確認（インスタンス化せずにProtocol準拠を確認）
        assert hasattr(YagmailAdapter, 'send')
        assert hasattr(YagmailAdapter, 'test')
        assert hasattr(YagmailAdapter, 'send_custom')


# =============================================================================
# 既存テスト
# =============================================================================


class TestCreateWaitUsecase:
    """create_wait_usecase()のテスト"""

    def test_create_wait_usecase_returns_usecase(self):
        """create_wait_usecaseがWaitEssayUseCaseを返す"""
        from usecases.factories import create_wait_usecase
        from usecases.wait_essay import WaitEssayUseCase

        usecase = create_wait_usecase()
        assert isinstance(usecase, WaitEssayUseCase)

    def test_create_wait_usecase_injects_dependencies(self):
        """依存性が注入される"""
        with (
            patch('usecases.factories.get_waiter_storage') as mock_get_waiter_storage,
            patch('usecases.factories.get_path_resolver') as mock_get_path_resolver,
            patch('usecases.factories.get_spawner') as mock_get_spawner,
        ):
            mock_waiter_storage = Mock()
            mock_path_resolver = Mock()
            mock_spawner = Mock()
            mock_get_waiter_storage.return_value = mock_waiter_storage
            mock_get_path_resolver.return_value = mock_path_resolver
            mock_get_spawner.return_value = mock_spawner

            from usecases.factories import create_wait_usecase

            _usecase = create_wait_usecase()

            mock_get_waiter_storage.assert_called_once()
            mock_get_path_resolver.assert_called_once()
            mock_get_spawner.assert_called_once()
