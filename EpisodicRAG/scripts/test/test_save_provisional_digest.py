#!/usr/bin/env python3
"""
ProvisionalDigestSaver 統合テスト
==================================

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

from save_provisional_digest import ProvisionalDigestSaver
from config import LEVEL_CONFIG


class TestProvisionalDigestSaver(unittest.TestCase):
    """ProvisionalDigestSaver の統合テスト"""

    def setUp(self):
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.digests_path = Path(self.temp_dir) / "Digests"
        self.digests_path.mkdir()

        # Provisionalディレクトリを作成
        self.weekly_provisional = self.digests_path / "1_Weekly" / "Provisional"
        self.weekly_provisional.mkdir(parents=True, exist_ok=True)

        # テスト用のsaverを作成（configをモック）
        # interfaces層に移動したため、パッチ先を変更
        with patch('interfaces.save_provisional_digest.DigestConfig') as mock_config_class:
            mock_config = MagicMock()
            mock_config.digests_path = self.digests_path
            # get_provisional_dir をモック
            mock_config.get_provisional_dir.return_value = self.weekly_provisional
            mock_config_class.return_value = mock_config
            self.saver = ProvisionalDigestSaver()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_load_individual_digests_from_list(self):
        """JSON文字列（リスト形式）からの読み込み"""
        json_str = '[{"source_file": "Loop0001.txt", "keywords": ["test"]}]'
        result = self.saver.load_individual_digests(json_str)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_file"], "Loop0001.txt")

    def test_load_individual_digests_from_dict(self):
        """JSON文字列（dict形式）からの読み込み"""
        json_str = '{"individual_digests": [{"source_file": "Loop0001.txt"}]}'
        result = self.saver.load_individual_digests(json_str)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    def test_load_individual_digests_empty_raises(self):
        """空文字列でValueError"""
        with self.assertRaises(ValueError):
            self.saver.load_individual_digests("")

    def test_merge_individual_digests(self):
        """マージ処理（重複は上書き）"""
        existing = [
            {"source_file": "Loop0001.txt", "keywords": ["old"]},
            {"source_file": "Loop0002.txt", "keywords": ["keep"]}
        ]
        new = [
            {"source_file": "Loop0001.txt", "keywords": ["new"]},
            {"source_file": "Loop0003.txt", "keywords": ["added"]}
        ]

        result = self.saver.merge_individual_digests(existing, new)

        self.assertEqual(len(result), 3)
        # Loop0001は上書きされる
        loop1 = next(d for d in result if d["source_file"] == "Loop0001.txt")
        self.assertEqual(loop1["keywords"], ["new"])

    def test_merge_individual_digests_missing_filename_raises(self):
        """source_fileキーがない場合ValueError"""
        existing = [{"keywords": ["test"]}]  # source_fileなし
        new = [{"source_file": "Loop0001.txt"}]

        with self.assertRaises(ValueError):
            self.saver.merge_individual_digests(existing, new)

    def test_save_provisional_new_file(self):
        """新規Provisionalファイルの保存"""
        individual_digests = [
            {"source_file": "Loop0001.txt", "keywords": ["test"]}
        ]

        saved_path = self.saver.save_provisional("weekly", individual_digests)

        self.assertTrue(saved_path.exists())
        self.assertIn("W0001_Individual.txt", saved_path.name)

        # 保存内容を検証
        with open(saved_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertIn("metadata", data)
        self.assertIn("individual_digests", data)
        self.assertEqual(len(data["individual_digests"]), 1)

    def test_save_provisional_append_mode(self):
        """追加モードでの保存"""
        # 最初の保存
        first_digests = [{"source_file": "Loop0001.txt", "keywords": ["first"]}]
        first_path = self.saver.save_provisional("weekly", first_digests)

        # 追加保存
        second_digests = [{"source_file": "Loop0002.txt", "keywords": ["second"]}]
        second_path = self.saver.save_provisional("weekly", second_digests, append=True)

        # 同じファイルに追加されている
        self.assertEqual(first_path, second_path)

        with open(second_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(len(data["individual_digests"]), 2)


if __name__ == "__main__":
    unittest.main()
