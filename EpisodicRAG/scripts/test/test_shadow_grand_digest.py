#!/usr/bin/env python3
"""
ShadowGrandDigestManager 統合テスト
====================================

一時ディレクトリを使用したファイルI/Oテスト
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Application層
from application.grand import ShadowGrandDigestManager


@pytest.fixture
def shadow_manager(temp_plugin_env):
    """ShadowGrandDigestManagerインスタンスを提供"""
    mock_config = MagicMock()
    mock_config.digests_path = temp_plugin_env.digests_path
    mock_config.loops_path = temp_plugin_env.loops_path
    mock_config.essences_path = temp_plugin_env.essences_path
    mock_config.plugin_root = temp_plugin_env.plugin_root
    mock_config.get_source_dir.return_value = temp_plugin_env.loops_path
    mock_config.get_source_pattern.return_value = "Loop*.txt"

    # last_digest_times.json を作成（DigestTimesTracker用）
    times_file = temp_plugin_env.config_dir / "last_digest_times.json"
    times_file.write_text("{}")

    with patch('application.grand.shadow_grand_digest.DigestConfig') as mock_config_class, \
         patch('application.grand.shadow_grand_digest.DigestTimesTracker') as mock_tracker_class:
        mock_config_class.return_value = mock_config
        mock_tracker = MagicMock()
        mock_tracker.load_or_create.return_value = {}
        mock_tracker_class.return_value = mock_tracker

        manager = ShadowGrandDigestManager(mock_config)
        manager._mock_tracker = mock_tracker  # テストからアクセス可能に
        manager._temp_env = temp_plugin_env  # 環境情報保持
        yield manager


class TestShadowGrandDigestManager:
    """ShadowGrandDigestManager の統合テスト"""

    @pytest.mark.integration
    def test_load_or_create_new_file(self, shadow_manager):
        """新規作成時の動作"""
        data = shadow_manager._io.load_or_create()

        assert shadow_manager.shadow_digest_file.exists()
        assert "metadata" in data
        assert "latest_digests" in data

    @pytest.mark.integration
    def test_load_or_create_existing_file(self, shadow_manager):
        """既存ファイル読み込み"""
        # テストデータを作成
        test_data = {
            "metadata": {"version": "test"},
            "latest_digests": {"weekly": {"overall_digest": {"test": True}}}
        }
        with open(shadow_manager.shadow_digest_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        data = shadow_manager._io.load_or_create()

        assert data["metadata"]["version"] == "test"

    @pytest.mark.integration
    def test_find_new_files_no_new(self, shadow_manager):
        """新しいファイルがない場合"""
        shadow_manager._mock_tracker.load_or_create.return_value = {}
        new_files = shadow_manager._detector.find_new_files("weekly")
        assert new_files == []

    @pytest.mark.integration
    def test_find_new_files_with_new(self, shadow_manager):
        """新しいLoopファイルがある場合"""
        # テストファイルを作成
        loops_path = shadow_manager._temp_env.loops_path
        (loops_path / "Loop0001_test.txt").write_text("{}")
        (loops_path / "Loop0002_test.txt").write_text("{}")

        shadow_manager._mock_tracker.load_or_create.return_value = {}
        new_files = shadow_manager._detector.find_new_files("weekly")

        assert len(new_files) == 2
        assert any("Loop0001" in f.name for f in new_files)

    @pytest.mark.integration
    def test_clear_shadow_level(self, shadow_manager):
        """Shadowレベルのクリア"""
        # まずデータを作成
        shadow_manager._io.load_or_create()

        # クリア
        shadow_manager.clear_shadow_level("weekly")

        # 確認
        data = shadow_manager._io.load_or_create()
        overall = data["latest_digests"]["weekly"]["overall_digest"]

        assert overall["source_files"] == []
        assert "PLACEHOLDER" in overall["abstract"]

    @pytest.mark.integration
    def test_get_shadow_digest_for_level_empty(self, shadow_manager):
        """空のShadowダイジェスト取得"""
        shadow_manager._io.load_or_create()

        result = shadow_manager.get_shadow_digest_for_level("weekly")

        assert result is None  # source_filesが空の場合はNone

    @pytest.mark.integration
    def test_get_shadow_digest_for_level_with_files(self, shadow_manager):
        """ファイルがあるShadowダイジェスト取得"""
        # テストデータを作成
        data = shadow_manager._io.load_or_create()
        data["latest_digests"]["weekly"]["overall_digest"]["source_files"] = ["Loop0001.txt"]
        shadow_manager._io.save(data)

        result = shadow_manager.get_shadow_digest_for_level("weekly")

        assert result is not None
        assert result["source_files"] == ["Loop0001.txt"]
