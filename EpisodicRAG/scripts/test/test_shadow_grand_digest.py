#!/usr/bin/env python3
"""
ShadowGrandDigestManager 統合テスト
====================================

一時ディレクトリを使用したファイルI/Oテスト
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Application層
from application.grand import ShadowGrandDigestManager

# Domain層
from domain.constants import LEVEL_NAMES


class TestShadowGrandDigestManager(unittest.TestCase):
    """ShadowGrandDigestManager の統合テスト"""

    def setUp(self):
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.digests_path = Path(self.temp_dir) / "Digests"
        self.loops_path = Path(self.temp_dir) / "Loops"
        self.essences_path = Path(self.temp_dir) / "Essences"
        self.plugin_dir = Path(self.temp_dir) / ".claude-plugin"

        self.digests_path.mkdir()
        self.loops_path.mkdir()
        self.essences_path.mkdir()
        self.plugin_dir.mkdir()

        # last_digest_times.json を作成（DigestTimesTracker用）
        times_file = self.plugin_dir / "last_digest_times.json"
        times_file.write_text("{}")

        # モック設定
        mock_config = MagicMock()
        mock_config.digests_path = self.digests_path
        mock_config.loops_path = self.loops_path
        mock_config.essences_path = self.essences_path
        mock_config.plugin_root = Path(self.temp_dir)

        with patch('application.grand.shadow_grand_digest.DigestConfig') as mock_config_class, \
             patch('application.grand.shadow_grand_digest.DigestTimesTracker') as mock_tracker_class:
            mock_config_class.return_value = mock_config
            mock_tracker = MagicMock()
            mock_tracker.load_or_create.return_value = {}
            mock_tracker_class.return_value = mock_tracker
            self.manager = ShadowGrandDigestManager(mock_config)
            self.mock_tracker = mock_tracker

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_get_template_structure(self):
        """テンプレートの構造確認"""
        template = self.manager.get_template()

        self.assertIn("metadata", template)
        self.assertIn("latest_digests", template)
        self.assertEqual(set(template["latest_digests"].keys()), set(LEVEL_NAMES))

        # 各レベルにoverall_digestがある
        for level in LEVEL_NAMES:
            self.assertIn("overall_digest", template["latest_digests"][level])

    def test_load_or_create_new_file(self):
        """新規作成時の動作"""
        data = self.manager.load_or_create()

        self.assertTrue(self.manager.shadow_digest_file.exists())
        self.assertIn("metadata", data)
        self.assertIn("latest_digests", data)

    def test_load_or_create_existing_file(self):
        """既存ファイル読み込み"""
        # テストデータを作成
        test_data = {
            "metadata": {"version": "test"},
            "latest_digests": {"weekly": {"overall_digest": {"test": True}}}
        }
        with open(self.manager.shadow_digest_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        data = self.manager.load_or_create()

        self.assertEqual(data["metadata"]["version"], "test")

    def test_create_empty_overall_digest(self):
        """プレースホルダー付きoverall_digest生成"""
        overall = self.manager._create_empty_overall_digest()

        self.assertIn("timestamp", overall)
        self.assertIn("source_files", overall)
        self.assertIn("keywords", overall)
        self.assertIn("abstract", overall)
        self.assertIn("impression", overall)
        self.assertEqual(overall["source_files"], [])
        self.assertTrue("PLACEHOLDER" in overall["abstract"])

    def test_find_new_files_no_new(self):
        """新しいファイルがない場合"""
        self.mock_tracker.load_or_create.return_value = {}
        new_files = self.manager.find_new_files("weekly")
        self.assertEqual(new_files, [])

    def test_find_new_files_with_new(self):
        """新しいLoopファイルがある場合"""
        # テストファイルを作成
        (self.loops_path / "Loop0001_test.txt").write_text("{}")
        (self.loops_path / "Loop0002_test.txt").write_text("{}")

        self.mock_tracker.load_or_create.return_value = {}
        new_files = self.manager.find_new_files("weekly")

        self.assertEqual(len(new_files), 2)
        self.assertTrue(any("Loop0001" in f.name for f in new_files))

    def test_clear_shadow_level(self):
        """Shadowレベルのクリア"""
        # まずデータを作成
        self.manager.load_or_create()

        # クリア
        self.manager.clear_shadow_level("weekly")

        # 確認
        data = self.manager.load_or_create()
        overall = data["latest_digests"]["weekly"]["overall_digest"]

        self.assertEqual(overall["source_files"], [])
        self.assertTrue("PLACEHOLDER" in overall["abstract"])

    def test_get_shadow_digest_for_level_empty(self):
        """空のShadowダイジェスト取得"""
        self.manager.load_or_create()

        result = self.manager.get_shadow_digest_for_level("weekly")

        self.assertIsNone(result)  # source_filesが空の場合はNone

    def test_get_shadow_digest_for_level_with_files(self):
        """ファイルがあるShadowダイジェスト取得"""
        # テストデータを作成
        data = self.manager.load_or_create()
        data["latest_digests"]["weekly"]["overall_digest"]["source_files"] = ["Loop0001.txt"]
        self.manager.save(data)

        result = self.manager.get_shadow_digest_for_level("weekly")

        self.assertIsNotNone(result)
        self.assertEqual(result["source_files"], ["Loop0001.txt"])


if __name__ == "__main__":
    unittest.main()
