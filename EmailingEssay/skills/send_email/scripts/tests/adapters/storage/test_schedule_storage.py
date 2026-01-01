# tests/adapters/storage/test_schedule_storage.py
"""
ScheduleStorageAdapter のテスト

Stage 5.2: ストレージアダプター責務分離
"""

import json
import os
import sys
from pathlib import Path

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from adapters.storage.path_resolver import PathResolverAdapter
from usecases.ports import ScheduleStoragePort


class TestScheduleStorageAdapter:
    """ScheduleStorageAdapter のテスト"""

    @pytest.fixture
    def path_resolver(self, tmp_path):
        """PathResolverAdapterを生成"""
        return PathResolverAdapter(base_dir=str(tmp_path))

    @pytest.fixture
    def adapter(self, path_resolver):
        """ScheduleStorageAdapterを生成"""
        from adapters.storage.schedule_storage import ScheduleStorageAdapter

        return ScheduleStorageAdapter(path_resolver)

    def test_conforms_to_protocol(self, adapter):
        """Protocol準拠"""
        assert isinstance(adapter, ScheduleStoragePort)

    def test_load_empty_returns_empty_list(self, adapter):
        """ファイルが存在しない場合は空リストを返す"""
        result = adapter.load_schedules()
        assert result == []

    def test_save_and_load_roundtrip(self, adapter):
        """保存と読み込みのラウンドトリップ"""
        schedules = [{"name": "test", "frequency": "daily", "time": "22:00"}]
        adapter.save_schedules(schedules)
        loaded = adapter.load_schedules()
        assert len(loaded) == 1
        assert loaded[0]["name"] == "test"
        assert loaded[0]["frequency"] == "daily"
        assert loaded[0]["time"] == "22:00"

    def test_save_creates_file(self, adapter, path_resolver):
        """保存するとファイルが作成される"""
        schedules = [{"name": "test", "frequency": "daily", "time": "22:00"}]
        adapter.save_schedules(schedules)

        schedules_file = Path(path_resolver.get_persistent_dir()) / "schedules.json"
        assert schedules_file.exists()

    def test_load_filters_invalid_entries(self, adapter, path_resolver):
        """無効なエントリはフィルタされる"""
        # 直接JSONを書き込んで無効なエントリを含める
        schedules_file = Path(path_resolver.get_persistent_dir()) / "schedules.json"
        data = {
            "schedules": [
                {"name": "valid", "frequency": "daily", "time": "22:00"},
                {"name": "invalid"},  # 必須フィールド欠落
                "not a dict",
            ]
        }
        with open(schedules_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        loaded = adapter.load_schedules()
        assert len(loaded) == 1
        assert loaded[0]["name"] == "valid"

    def test_load_empty_file_returns_empty_list(self, adapter, path_resolver):
        """空ファイルの場合は空リストを返す"""
        schedules_file = Path(path_resolver.get_persistent_dir()) / "schedules.json"
        schedules_file.write_text("")

        result = adapter.load_schedules()
        assert result == []

    def test_load_corrupted_json_returns_empty_list(self, adapter, path_resolver):
        """破損JSONの場合は空リストを返す（バックアップなし）"""
        schedules_file = Path(path_resolver.get_persistent_dir()) / "schedules.json"
        schedules_file.write_text("{invalid json")

        result = adapter.load_schedules()
        assert result == []

    def test_backup_and_recovery(self, adapter, path_resolver):
        """バックアップから復旧できる"""
        # 初回保存（ファイル作成）
        schedules = [{"name": "original", "frequency": "daily", "time": "22:00"}]
        adapter.save_schedules(schedules)

        # 2回目の保存でバックアップを強制作成
        schedules_updated = [{"name": "updated", "frequency": "daily", "time": "23:00"}]
        adapter.save_schedules(schedules_updated, force_backup=True)

        # ファイルを破損させる
        schedules_file = Path(path_resolver.get_persistent_dir()) / "schedules.json"
        schedules_file.write_text("{corrupted")

        # 読み込み（バックアップから復旧されるはず）
        # バックアップには「original」が保存されている
        loaded = adapter.load_schedules()
        assert len(loaded) == 1
        assert loaded[0]["name"] == "original"

    def test_multiple_schedules(self, adapter):
        """複数スケジュールの保存・読み込み"""
        schedules = [
            {"name": "daily_essay", "frequency": "daily", "time": "22:00"},
            {"name": "weekly_essay", "frequency": "weekly", "time": "10:00", "weekday": "monday"},
        ]
        adapter.save_schedules(schedules)
        loaded = adapter.load_schedules()
        assert len(loaded) == 2

    def test_overwrite_existing(self, adapter):
        """既存データの上書き"""
        # 初回保存
        adapter.save_schedules([{"name": "first", "frequency": "daily", "time": "22:00"}])

        # 上書き
        adapter.save_schedules([{"name": "second", "frequency": "weekly", "time": "10:00"}])

        loaded = adapter.load_schedules()
        assert len(loaded) == 1
        assert loaded[0]["name"] == "second"
