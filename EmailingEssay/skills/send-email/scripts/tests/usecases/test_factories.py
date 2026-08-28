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
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from usecases.ports import (
    LedgerPort,
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

    def test_schedule_storage_conforms_to_protocol(self, tmp_path):
        """ScheduleStorageAdapterがScheduleStoragePortに準拠する"""
        from adapters.storage import PathResolverAdapter, ScheduleStorageAdapter

        path_resolver = PathResolverAdapter(base_dir=str(tmp_path))
        storage = ScheduleStorageAdapter(path_resolver)
        assert isinstance(storage, ScheduleStoragePort)

    def test_waiter_storage_conforms_to_protocol(self, tmp_path):
        """WaiterStorageAdapterがWaiterStoragePortに準拠する"""
        from adapters.storage import PathResolverAdapter, WaiterStorageAdapter

        path_resolver = PathResolverAdapter(base_dir=str(tmp_path))
        storage = WaiterStorageAdapter(path_resolver)
        assert isinstance(storage, WaiterStoragePort)

    def test_path_resolver_conforms_to_protocol(self):
        """PathResolverAdapterがPathResolverPortに準拠する"""
        from adapters.storage import PathResolverAdapter

        resolver = PathResolverAdapter()
        assert isinstance(resolver, PathResolverPort)

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
        assert hasattr(YagmailAdapter, "send")
        assert hasattr(YagmailAdapter, "test")
        assert hasattr(YagmailAdapter, "send_custom")


# =============================================================================
# 既存テスト
# =============================================================================


class TestFactoryTypeSafety:
    """ファクトリ関数の型安全性テスト（Stage 6）"""

    def test_get_scheduler_returns_scheduler_port(self):
        """get_scheduler()がSchedulerPort準拠インスタンスを返す"""
        from usecases.factories import AdapterRegistry, get_scheduler

        AdapterRegistry.clear()
        scheduler = get_scheduler()
        assert isinstance(scheduler, SchedulerPort)

    def test_get_schedule_storage_returns_storage_port(self):
        """get_schedule_storage()がScheduleStoragePort準拠インスタンスを返す"""
        from usecases.factories import AdapterRegistry, get_schedule_storage

        AdapterRegistry.clear()
        storage = get_schedule_storage()
        assert isinstance(storage, ScheduleStoragePort)

    def test_get_waiter_storage_returns_storage_port(self):
        """get_waiter_storage()がWaiterStoragePort準拠インスタンスを返す"""
        from usecases.factories import AdapterRegistry, get_waiter_storage

        AdapterRegistry.clear()
        storage = get_waiter_storage()
        assert isinstance(storage, WaiterStoragePort)

    def test_get_ledger_returns_ledger_port(self):
        """get_ledger()がLedgerPort準拠インスタンスを返す"""
        from usecases.factories import AdapterRegistry, get_ledger

        AdapterRegistry.clear()
        ledger = get_ledger()
        assert isinstance(ledger, LedgerPort)

    def test_get_path_resolver_returns_resolver_port(self):
        """get_path_resolver()がPathResolverPort準拠インスタンスを返す"""
        from usecases.factories import AdapterRegistry, get_path_resolver

        AdapterRegistry.clear()
        resolver = get_path_resolver()
        assert isinstance(resolver, PathResolverPort)

    def test_get_spawner_returns_spawner_port(self):
        """get_spawner()がProcessSpawnerPort準拠インスタンスを返す"""
        from usecases.factories import AdapterRegistry, get_spawner

        AdapterRegistry.clear()
        spawner = get_spawner()
        assert isinstance(spawner, ProcessSpawnerPort)


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
            patch("usecases.factories.get_waiter_storage") as mock_get_waiter_storage,
            patch("usecases.factories.get_path_resolver") as mock_get_path_resolver,
            patch("usecases.factories.get_spawner") as mock_get_spawner,
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


# =============================================================================
# Stage 4: 受信箱ファクトリ（実接続はしない）
# =============================================================================


class TestInboxFactory:
    """get_inbox / create_ingest_replies_usecase のテスト"""

    @staticmethod
    def _set_env(monkeypatch):
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "test@test.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "testpass")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@test.com")

        from domain.config import Config

        Config.reset()

    def test_get_inbox_returns_inbox_port(self, monkeypatch):
        """get_inbox()がInboxPort準拠インスタンスを返す"""
        self._set_env(monkeypatch)

        from usecases.factories import AdapterRegistry, get_inbox
        from usecases.ports import InboxPort

        AdapterRegistry.clear()
        assert isinstance(get_inbox(), InboxPort)

    def test_get_inbox_uses_registry(self, monkeypatch):
        """get_inboxがレジストリを使用する（シングルトン）"""
        self._set_env(monkeypatch)

        from usecases.factories import AdapterRegistry, get_inbox

        AdapterRegistry.clear()
        assert get_inbox() is get_inbox()

    def test_get_inbox_returns_imap_adapter(self, monkeypatch):
        """実体は ImapInboxAdapter（構築だけでは接続しない）"""
        self._set_env(monkeypatch)

        from adapters.mail import ImapInboxAdapter
        from usecases.factories import AdapterRegistry, get_inbox

        AdapterRegistry.clear()
        assert isinstance(get_inbox(), ImapInboxAdapter)

    def test_create_ingest_replies_usecase_injects_dependencies(self, monkeypatch):
        """IngestRepliesUseCase に inbox / ledger / recipient が注入される"""
        self._set_env(monkeypatch)

        with (
            patch("usecases.factories.get_inbox") as mock_get_inbox,
            patch("usecases.factories.get_ledger") as mock_get_ledger,
        ):
            mock_get_inbox.return_value = Mock()
            mock_get_ledger.return_value = Mock()

            from usecases.factories import create_ingest_replies_usecase
            from usecases.ingest_replies import IngestRepliesUseCase

            usecase = create_ingest_replies_usecase()

            assert isinstance(usecase, IngestRepliesUseCase)
            mock_get_inbox.assert_called_once()
            mock_get_ledger.assert_called_once()
            assert usecase._recipient == "recv@test.com"
