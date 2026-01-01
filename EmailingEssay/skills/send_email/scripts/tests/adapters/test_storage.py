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
