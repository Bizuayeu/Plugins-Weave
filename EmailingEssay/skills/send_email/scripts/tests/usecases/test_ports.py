# tests/usecases/test_ports.py
"""
ポートインターフェース分離のテスト

StoragePortを3つの責務別Protocolに分離することをテストする。
"""

import os
import sys

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestScheduleStoragePort:
    """ScheduleStoragePortのテスト"""

    def test_protocol_has_load_schedules(self):
        """load_schedulesメソッドを持つ"""
        from usecases.ports import ScheduleStoragePort

        assert hasattr(ScheduleStoragePort, 'load_schedules')

    def test_protocol_has_save_schedules(self):
        """save_schedulesメソッドを持つ"""
        from usecases.ports import ScheduleStoragePort

        assert hasattr(ScheduleStoragePort, 'save_schedules')


class TestWaiterStoragePort:
    """WaiterStoragePortのテスト"""

    def test_protocol_has_register_waiter(self):
        """register_waiterメソッドを持つ"""
        from usecases.ports import WaiterStoragePort

        assert hasattr(WaiterStoragePort, 'register_waiter')

    def test_protocol_has_get_active_waiters(self):
        """get_active_waitersメソッドを持つ"""
        from usecases.ports import WaiterStoragePort

        assert hasattr(WaiterStoragePort, 'get_active_waiters')


class TestPathResolverPort:
    """PathResolverPortのテスト"""

    def test_protocol_has_get_persistent_dir(self):
        """get_persistent_dirメソッドを持つ"""
        from usecases.ports import PathResolverPort

        assert hasattr(PathResolverPort, 'get_persistent_dir')

    def test_protocol_has_get_runners_dir(self):
        """get_runners_dirメソッドを持つ"""
        from usecases.ports import PathResolverPort

        assert hasattr(PathResolverPort, 'get_runners_dir')


class TestStorageAdaptersImplementPorts:
    """各ストレージアダプターがProtocolを実装しているかテスト"""

    def test_schedule_storage_implements_protocol(self, tmp_path):
        """ScheduleStorageAdapterがScheduleStoragePortを実装"""
        from adapters.storage import PathResolverAdapter, ScheduleStorageAdapter
        from usecases.ports import ScheduleStoragePort

        path_resolver = PathResolverAdapter(base_dir=str(tmp_path))
        adapter = ScheduleStorageAdapter(path_resolver)
        assert isinstance(adapter, ScheduleStoragePort)

    def test_waiter_storage_implements_protocol(self, tmp_path):
        """WaiterStorageAdapterがWaiterStoragePortを実装"""
        from adapters.storage import PathResolverAdapter, WaiterStorageAdapter
        from usecases.ports import WaiterStoragePort

        path_resolver = PathResolverAdapter(base_dir=str(tmp_path))
        adapter = WaiterStorageAdapter(path_resolver)
        assert isinstance(adapter, WaiterStoragePort)

    def test_path_resolver_implements_protocol(self, tmp_path):
        """PathResolverAdapterがPathResolverPortを実装"""
        from adapters.storage import PathResolverAdapter
        from usecases.ports import PathResolverPort

        adapter = PathResolverAdapter(base_dir=str(tmp_path))
        assert isinstance(adapter, PathResolverPort)
