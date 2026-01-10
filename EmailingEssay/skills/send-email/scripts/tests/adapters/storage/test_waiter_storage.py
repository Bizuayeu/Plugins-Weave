# tests/adapters/storage/test_waiter_storage.py
"""
WaiterStorageAdapter のテスト

Stage 5.3: ストレージアダプター責務分離
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)

from adapters.storage.path_resolver import PathResolverAdapter
from usecases.ports import WaiterStoragePort


class TestWaiterStorageAdapter:
    """WaiterStorageAdapter のテスト"""

    @pytest.fixture
    def path_resolver(self, tmp_path):
        """PathResolverAdapterを生成"""
        return PathResolverAdapter(base_dir=str(tmp_path))

    @pytest.fixture
    def adapter(self, path_resolver):
        """WaiterStorageAdapterを生成"""
        from adapters.storage.waiter_storage import WaiterStorageAdapter

        return WaiterStorageAdapter(path_resolver)

    def test_conforms_to_protocol(self, adapter):
        """Protocol準拠"""
        assert isinstance(adapter, WaiterStoragePort)

    def test_get_active_waiters_empty(self, adapter):
        """ファイルが存在しない場合は空リストを返す"""
        result = adapter.get_active_waiters()
        assert result == []

    def test_register_waiter_creates_file(self, adapter, path_resolver):
        """待機プロセスを登録するとファイルが作成される"""
        adapter.register_waiter(pid=12345, target_time="12:00", theme="test")

        waiters_file = Path(path_resolver.get_persistent_dir()) / "active_waiters.json"
        assert waiters_file.exists()

    def test_register_waiter_stores_data(self, adapter, path_resolver):
        """登録データがファイルに保存される"""
        adapter.register_waiter(pid=12345, target_time="12:00", theme="test theme")

        waiters_file = Path(path_resolver.get_persistent_dir()) / "active_waiters.json"
        with open(waiters_file, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["waiters"]) == 1
        assert data["waiters"][0]["pid"] == 12345
        assert data["waiters"][0]["target_time"] == "12:00"
        assert data["waiters"][0]["theme"] == "test theme"
        assert "registered_at" in data["waiters"][0]

    def test_register_multiple_waiters(self, adapter, path_resolver):
        """複数の待機プロセスを登録できる"""
        adapter.register_waiter(pid=111, target_time="10:00", theme="theme1")
        adapter.register_waiter(pid=222, target_time="11:00", theme="theme2")
        adapter.register_waiter(pid=333, target_time="12:00", theme="theme3")

        waiters_file = Path(path_resolver.get_persistent_dir()) / "active_waiters.json"
        with open(waiters_file, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["waiters"]) == 3

    def test_get_active_waiters_returns_alive_processes(self, adapter):
        """生存プロセスのみを返す"""
        # 現在のプロセスIDを使用（確実に生存）
        current_pid = os.getpid()
        adapter.register_waiter(pid=current_pid, target_time="12:00", theme="test")

        result = adapter.get_active_waiters()
        assert len(result) == 1
        assert result[0]["pid"] == current_pid

    def test_get_active_waiters_filters_dead_processes(self, adapter, path_resolver):
        """死亡プロセスはフィルタされる"""
        # 存在しないPIDで登録（99999999は通常存在しない）
        adapter.register_waiter(pid=99999999, target_time="12:00", theme="dead")

        result = adapter.get_active_waiters()
        assert len(result) == 0

        # ファイルも更新されている（死亡プロセスが削除されている）
        waiters_file = Path(path_resolver.get_persistent_dir()) / "active_waiters.json"
        with open(waiters_file, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["waiters"]) == 0

    def test_get_active_waiters_validates_entries(self, adapter, path_resolver):
        """無効なエントリはフィルタされる"""
        # 直接JSONを書き込んで無効なエントリを含める
        waiters_file = Path(path_resolver.get_persistent_dir()) / "active_waiters.json"
        current_pid = os.getpid()
        data = {
            "waiters": [
                {
                    "pid": current_pid,
                    "target_time": "12:00",
                    "theme": "valid",
                    "registered_at": datetime.now().isoformat(),
                },
                {"pid": current_pid},  # 必須フィールド欠落
                "not a dict",
            ]
        }
        with open(waiters_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        result = adapter.get_active_waiters()
        assert len(result) == 1
        assert result[0]["theme"] == "valid"

    def test_get_active_waiters_handles_empty_file(self, adapter, path_resolver):
        """空ファイルの場合は空リストを返す"""
        waiters_file = Path(path_resolver.get_persistent_dir()) / "active_waiters.json"
        waiters_file.write_text("")

        result = adapter.get_active_waiters()
        assert result == []

    def test_get_active_waiters_handles_corrupted_json(self, adapter, path_resolver):
        """破損JSONの場合は空リストを返す"""
        waiters_file = Path(path_resolver.get_persistent_dir()) / "active_waiters.json"
        waiters_file.write_text("{invalid json")

        result = adapter.get_active_waiters()
        assert result == []
