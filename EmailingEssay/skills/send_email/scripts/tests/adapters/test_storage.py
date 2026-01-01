# tests/adapters/test_storage.py
"""
JsonStorageAdapter のユニットテスト

Phase 9.1: TDD補完 - Phase 9で漏れたテストを追加
"""
import pytest
import tempfile
import os
import json
import sys

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.storage.json_adapter import JsonStorageAdapter


class TestJsonStorageAdapter:
    """JsonStorageAdapter のテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def adapter(self, temp_dir):
        """テスト用アダプターを作成"""
        return JsonStorageAdapter(base_dir=temp_dir)

    def test_get_persistent_dir_creates_directory(self, adapter, temp_dir):
        """永続化ディレクトリが作成される"""
        result = adapter.get_persistent_dir()
        assert result == temp_dir
        assert os.path.exists(result)

    def test_get_runners_dir_creates_directory(self, adapter, temp_dir):
        """ランナーディレクトリが作成される"""
        result = adapter.get_runners_dir()
        expected = os.path.join(temp_dir, "runners")
        assert result == expected
        assert os.path.exists(result)

    def test_load_schedules_empty_file(self, adapter):
        """ファイルがない場合は空リスト"""
        result = adapter.load_schedules()
        assert result == []

    def test_save_and_load_schedules(self, adapter):
        """保存したスケジュールを読み込める"""
        schedules = [
            {"name": "test1", "frequency": "daily", "time": "09:00"},
            {"name": "test2", "frequency": "weekly", "time": "10:00", "weekday": "monday"}
        ]
        adapter.save_schedules(schedules)
        result = adapter.load_schedules()
        assert len(result) == 2
        assert result[0]["name"] == "test1"
        assert result[1]["weekday"] == "monday"

    def test_save_schedules_creates_valid_json(self, adapter, temp_dir):
        """保存ファイルが有効なJSON"""
        schedules = [{"name": "test", "theme": "日本語テーマ"}]
        adapter.save_schedules(schedules)

        file_path = os.path.join(temp_dir, "schedules.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "schedules" in data
        assert data["schedules"][0]["theme"] == "日本語テーマ"

    def test_default_persistent_dir(self):
        """デフォルトパスが正しく構築される"""
        adapter = JsonStorageAdapter()
        result = adapter.get_persistent_dir()
        assert ".claude" in result or ".emailingessay" in result


class TestJsonStorageAdapterErrorRecovery:
    """JSON破損時の復旧処理テスト（Item 1）"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def adapter(self, temp_dir):
        """テスト用アダプターを作成"""
        return JsonStorageAdapter(base_dir=temp_dir)

    def test_load_schedules_with_corrupted_json_returns_empty_list(self, adapter, temp_dir):
        """破損したJSONファイルで空リストを返す"""
        file_path = os.path.join(temp_dir, "schedules.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("{invalid json content")

        result = adapter.load_schedules()
        assert result == []

    def test_load_schedules_with_empty_file_returns_empty_list(self, adapter, temp_dir):
        """空ファイルで空リストを返す"""
        file_path = os.path.join(temp_dir, "schedules.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("")

        result = adapter.load_schedules()
        assert result == []

    def test_load_schedules_with_missing_schedules_key_returns_empty(self, adapter, temp_dir):
        """schedulesキーがないJSONで空リストを返す"""
        file_path = os.path.join(temp_dir, "schedules.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"other_key": "value"}, f)

        result = adapter.load_schedules()
        assert result == []

    def test_load_schedules_with_whitespace_only_returns_empty_list(self, adapter, temp_dir):
        """空白のみのファイルで空リストを返す"""
        file_path = os.path.join(temp_dir, "schedules.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("   \n\t  ")

        result = adapter.load_schedules()
        assert result == []

    def test_load_schedules_with_non_dict_json_returns_empty(self, adapter, temp_dir):
        """JSONがdict以外（配列など）の場合に空リストを返す"""
        file_path = os.path.join(temp_dir, "schedules.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(["item1", "item2"], f)

        result = adapter.load_schedules()
        assert result == []


class TestJsonStorageAdapterWaiterTracking:
    """待機プロセストラッキング機能のテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def adapter(self, temp_dir):
        """テスト用アダプターを作成"""
        return JsonStorageAdapter(base_dir=temp_dir)

    def test_get_active_waiters_file_path(self, adapter, temp_dir):
        """待機プロセスファイルのパスが正しい"""
        result = adapter.get_active_waiters_file()
        expected = os.path.join(temp_dir, "active_waiters.json")
        assert result == expected

    def test_get_active_waiters_empty_when_no_file(self, adapter):
        """ファイルがない場合は空リストを返す"""
        result = adapter.get_active_waiters()
        assert result == []

    def test_register_waiter_creates_file(self, adapter, temp_dir):
        """register_waiterでファイルが作成される"""
        adapter.register_waiter(pid=12345, target_time="09:00", theme="test theme")

        file_path = os.path.join(temp_dir, "active_waiters.json")
        assert os.path.exists(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "waiters" in data
        assert len(data["waiters"]) == 1
        assert data["waiters"][0]["pid"] == 12345
        assert data["waiters"][0]["target_time"] == "09:00"
        assert data["waiters"][0]["theme"] == "test theme"

    def test_register_multiple_waiters(self, adapter, temp_dir):
        """複数の待機プロセスを登録できる"""
        adapter.register_waiter(pid=100, target_time="09:00", theme="theme1")
        adapter.register_waiter(pid=200, target_time="10:00", theme="theme2")

        file_path = os.path.join(temp_dir, "active_waiters.json")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["waiters"]) == 2
        pids = [w["pid"] for w in data["waiters"]]
        assert 100 in pids
        assert 200 in pids

    def test_get_active_waiters_filters_dead_processes(self, adapter, temp_dir):
        """死亡したプロセスは除外される"""
        # 存在しないPIDを登録
        fake_pid = 999999999
        file_path = os.path.join(temp_dir, "active_waiters.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({
                "waiters": [
                    {"pid": fake_pid, "target_time": "09:00", "theme": "test", "registered_at": "2025-01-01T00:00:00"}
                ]
            }, f)

        # get_active_waitersは死亡プロセスを除外する
        result = adapter.get_active_waiters()
        assert len(result) == 0

    def test_is_process_alive_returns_false_for_nonexistent_pid(self, adapter):
        """存在しないPIDに対してFalseを返す"""
        # 非常に大きなPIDは存在しないはず
        result = adapter._is_process_alive(999999999)
        assert result is False

    def test_is_process_alive_returns_true_for_current_process(self, adapter):
        """現在のプロセスに対してTrueを返す"""
        import os
        current_pid = os.getpid()
        result = adapter._is_process_alive(current_pid)
        assert result is True
