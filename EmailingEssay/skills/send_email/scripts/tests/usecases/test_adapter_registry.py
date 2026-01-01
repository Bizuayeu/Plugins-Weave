# tests/usecases/test_adapter_registry.py
"""
AdapterRegistry TDD tests

シングルトンレジストリのテスト。
"""

import pytest


class TestAdapterRegistry:
    """AdapterRegistry singleton tests"""

    def test_get_or_create_returns_same_instance(self):
        """同じキーは同じインスタンスを返す"""
        from usecases.factories import AdapterRegistry

        AdapterRegistry.clear()
        factory_calls = []

        def factory():
            factory_calls.append(1)
            return object()

        instance1 = AdapterRegistry.get_or_create("test", factory)
        instance2 = AdapterRegistry.get_or_create("test", factory)

        assert instance1 is instance2
        assert len(factory_calls) == 1  # ファクトリは1回だけ呼ばれる

    def test_different_keys_return_different_instances(self):
        """異なるキーは異なるインスタンスを返す"""
        from usecases.factories import AdapterRegistry

        AdapterRegistry.clear()

        instance1 = AdapterRegistry.get_or_create("key1", object)
        instance2 = AdapterRegistry.get_or_create("key2", object)

        assert instance1 is not instance2

    def test_clear_removes_all_instances(self):
        """clearで全インスタンス削除"""
        from usecases.factories import AdapterRegistry

        AdapterRegistry.clear()
        instance1 = AdapterRegistry.get_or_create("test", object)
        AdapterRegistry.clear()
        instance2 = AdapterRegistry.get_or_create("test", object)

        assert instance1 is not instance2

    def test_get_mail_adapter_uses_registry(self, monkeypatch):
        """get_mail_adapterがレジストリを使用"""
        # 環境変数を設定（YagmailAdapterが必要とする）
        monkeypatch.setenv("ESSAY_SENDER_EMAIL", "test@test.com")
        monkeypatch.setenv("ESSAY_APP_PASSWORD", "testpass")
        monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", "recv@test.com")

        from domain.config import Config

        Config.reset()

        from usecases.factories import AdapterRegistry, get_mail_adapter

        AdapterRegistry.clear()
        adapter1 = get_mail_adapter()
        adapter2 = get_mail_adapter()

        assert adapter1 is adapter2

    def test_get_schedule_storage_uses_registry(self):
        """get_schedule_storageがレジストリを使用"""
        from usecases.factories import AdapterRegistry, get_schedule_storage

        AdapterRegistry.clear()
        storage1 = get_schedule_storage()
        storage2 = get_schedule_storage()

        assert storage1 is storage2

    def test_get_waiter_storage_uses_registry(self):
        """get_waiter_storageがレジストリを使用"""
        from usecases.factories import AdapterRegistry, get_waiter_storage

        AdapterRegistry.clear()
        storage1 = get_waiter_storage()
        storage2 = get_waiter_storage()

        assert storage1 is storage2

    def test_get_path_resolver_uses_registry(self):
        """get_path_resolverがレジストリを使用"""
        from usecases.factories import AdapterRegistry, get_path_resolver

        AdapterRegistry.clear()
        resolver1 = get_path_resolver()
        resolver2 = get_path_resolver()

        assert resolver1 is resolver2

    def test_get_scheduler_uses_registry(self):
        """get_schedulerがレジストリを使用"""
        from usecases.factories import AdapterRegistry, get_scheduler

        AdapterRegistry.clear()
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()

        assert scheduler1 is scheduler2

    def test_get_spawner_uses_registry(self):
        """get_spawnerがレジストリを使用"""
        from usecases.factories import AdapterRegistry, get_spawner

        AdapterRegistry.clear()
        spawner1 = get_spawner()
        spawner2 = get_spawner()

        assert spawner1 is spawner2
