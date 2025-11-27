#!/usr/bin/env python3
"""
DigestTimesTracker 統合テスト
==============================

一時ディレクトリを使用したファイルI/Oテスト
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Application層
from application.tracking import DigestTimesTracker


class TestDigestTimesTracker(unittest.TestCase):
    """DigestTimesTracker の統合テスト"""

    def setUp(self):
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self.claude_plugin_dir = self.plugin_root / ".claude-plugin"
        self.claude_plugin_dir.mkdir()

        # モック設定
        self.mock_config = MagicMock()
        self.mock_config.plugin_root = self.plugin_root

        self.tracker = DigestTimesTracker(self.mock_config)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_load_or_create_empty(self):
        """空の状態からの読み込み"""
        data = self.tracker.load_or_create()

        # 全レベルが初期化されていることを確認
        self.assertIn("weekly", data)
        self.assertIn("centurial", data)

    def test_save_and_load(self):
        """保存と読み込み"""
        input_files = ["Loop0001_Test.txt", "Loop0002_Test.txt"]
        self.tracker.save("weekly", input_files)

        data = self.tracker.load_or_create()

        self.assertIn("timestamp", data["weekly"])
        self.assertEqual(data["weekly"]["last_processed"], "Loop0002")

    def test_extract_file_numbers(self):
        """ファイル番号抽出"""
        files = ["Loop0001_A.txt", "Loop0003_B.txt"]
        numbers = self.tracker.extract_file_numbers("weekly", files)

        self.assertEqual(numbers, ["Loop0001", "Loop0003"])

    def test_extract_file_numbers_monthly(self):
        """Monthlyレベルのファイル番号抽出（Wプレフィックスは4桁維持）"""
        files = ["W0001_A.txt", "W0005_B.txt"]
        numbers = self.tracker.extract_file_numbers("monthly", files)

        # ソースファイル(Weekly)の形式を維持: W0001, W0005
        self.assertEqual(numbers, ["W0001", "W0005"])


if __name__ == "__main__":
    unittest.main()
