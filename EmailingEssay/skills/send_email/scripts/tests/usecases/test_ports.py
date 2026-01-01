# tests/usecases/test_ports.py
"""
ポートインターフェース分離のテスト

StoragePortを3つの責務別Protocolに分離することをテストする。
"""
import pytest
import sys
import os

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


class TestJsonStorageAdapterImplementsAllPorts:
    """JsonStorageAdapterが全Protocolを実装しているかテスト"""

    def test_implements_schedule_storage(self, tmp_path):
        """ScheduleStoragePortを実装"""
        from usecases.ports import ScheduleStoragePort
        from adapters.storage import JsonStorageAdapter

        adapter = JsonStorageAdapter(base_dir=str(tmp_path))
        assert isinstance(adapter, ScheduleStoragePort)

    def test_implements_waiter_storage(self, tmp_path):
        """WaiterStoragePortを実装"""
        from usecases.ports import WaiterStoragePort
        from adapters.storage import JsonStorageAdapter

        adapter = JsonStorageAdapter(base_dir=str(tmp_path))
        assert isinstance(adapter, WaiterStoragePort)

    def test_implements_path_resolver(self, tmp_path):
        """PathResolverPortを実装"""
        from usecases.ports import PathResolverPort
        from adapters.storage import JsonStorageAdapter

        adapter = JsonStorageAdapter(base_dir=str(tmp_path))
        assert isinstance(adapter, PathResolverPort)
