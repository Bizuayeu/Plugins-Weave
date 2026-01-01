# tests/adapters/test_storage.py
"""
JsonStorageAdapter のユニットテスト

Phase 9.1: TDD補完 - Phase 9で漏れたテストを追加
"""

import json
import os
import sys
import tempfile

import pytest

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
            {"name": "test2", "frequency": "weekly", "time": "10:00", "weekday": "monday"},
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
            json.dump(
                {
                    "waiters": [
                        {
                            "pid": fake_pid,
                            "target_time": "09:00",
                            "theme": "test",
                            "registered_at": "2025-01-01T00:00:00",
                        }
                    ]
                },
                f,
            )

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


class TestTypeSafety:
    """型安全性テスト（Phase 3）"""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def adapter(self, temp_dir):
        return JsonStorageAdapter(base_dir=temp_dir)

    def test_load_schedules_returns_schedule_entry_list(self, adapter, temp_dir):
        """戻り値がScheduleEntryのリストであること"""
        from usecases.ports import ScheduleEntry

        # サンプルデータ作成
        sample = {"schedules": [{"name": "test", "frequency": "daily", "time": "09:00"}]}
        file_path = os.path.join(temp_dir, "schedules.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sample, f)

        result = adapter.load_schedules()

        assert isinstance(result, list)
        assert len(result) == 1
        # TypedDictのキーが存在することを確認
        assert "name" in result[0]
        assert "frequency" in result[0]
        assert "time" in result[0]

    def test_get_active_waiters_returns_waiter_entry_list(self, adapter, temp_dir):
        """戻り値がWaiterEntryのリストであること"""
        import os as os_module

        from usecases.ports import WaiterEntry

        # 現在のプロセスPIDを使用（確実に存在する）
        current_pid = os_module.getpid()

        # サンプルデータ作成
        sample = {
            "waiters": [
                {
                    "pid": current_pid,
                    "target_time": "09:00",
                    "theme": "test",
                    "registered_at": "2025-01-01T00:00:00",
                }
            ]
        }
        file_path = os.path.join(temp_dir, "active_waiters.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sample, f)

        result = adapter.get_active_waiters()

        assert isinstance(result, list)
        assert len(result) == 1
        # TypedDictのキーが存在することを確認
        assert "pid" in result[0]
        assert "target_time" in result[0]
        assert "theme" in result[0]
        assert "registered_at" in result[0]


class TestProcessCache:
    """プロセスキャッシュテスト（Phase 4）"""

    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def adapter(self, temp_dir):
        return JsonStorageAdapter(base_dir=temp_dir)

    def test_dead_process_removed_from_cache(self, adapter):
        """死亡プロセスがキャッシュから削除される"""
        import time

        # 存在しないPIDを登録
        fake_pid = 99999999
        adapter._process_cache[fake_pid] = (True, time.time() - 100)

        # キャッシュクリーンアップを発動
        adapter._cleanup_dead_processes()

        assert fake_pid not in adapter._process_cache

    def test_alive_process_remains_in_cache(self, adapter):
        """生存プロセスはキャッシュに残る"""
        import os as os_module
        import time

        current_pid = os_module.getpid()

        adapter._process_cache[current_pid] = (True, time.time())
        adapter._cleanup_dead_processes()

        assert current_pid in adapter._process_cache

    def test_cache_ttl_returns_cached_value(self, adapter):
        """TTL内はキャッシュから値を返す"""
        import time

        fake_pid = 99999999
        # 最近のタイムスタンプでキャッシュに登録（alive=Trueだが実際は存在しない）
        adapter._process_cache[fake_pid] = (True, time.time())

        # TTL内なのでキャッシュからTrueが返る（実際の生存チェックは行われない）
        result = adapter._is_process_alive_cached(fake_pid)
        assert result is True

    def test_cache_expired_rechecks_process(self, adapter):
        """TTL超過時は再チェック"""
        import time

        fake_pid = 99999999
        # 古いタイムスタンプでキャッシュに登録
        adapter._process_cache[fake_pid] = (True, time.time() - 100)

        # TTL超過なので実際に生存チェックが行われ、Falseが返る
        result = adapter._is_process_alive_cached(fake_pid)
        assert result is False
