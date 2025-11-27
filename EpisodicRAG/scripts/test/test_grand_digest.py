#!/usr/bin/env python3
"""
GrandDigestManager 統合テスト
==============================

一時ディレクトリを使用したファイルI/Oテスト
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# Application層
from application.grand import GrandDigestManager

# Domain層
from domain.constants import LEVEL_NAMES
from domain.exceptions import DigestError


class TestGrandDigestManager(unittest.TestCase):
    """GrandDigestManager の統合テスト"""

    def setUp(self):
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.essences_path = Path(self.temp_dir) / "Essences"
        self.essences_path.mkdir()

        # モック設定
        self.mock_config = MagicMock()
        self.mock_config.essences_path = self.essences_path

        self.manager = GrandDigestManager(self.mock_config)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_get_template_structure(self):
        """テンプレートの構造確認"""
        template = self.manager.get_template()

        self.assertIn("metadata", template)
        self.assertIn("major_digests", template)
        self.assertEqual(set(template["major_digests"].keys()), set(LEVEL_NAMES))

    def test_load_or_create_new(self):
        """新規作成時の動作"""
        data = self.manager.load_or_create()

        self.assertTrue(self.manager.grand_digest_file.exists())
        self.assertIn("metadata", data)

    def test_save_and_load(self):
        """保存と読み込みの整合性"""
        test_data = {"test": "data", "number": 123}
        self.manager.save(test_data)

        with open(self.manager.grand_digest_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)

        self.assertEqual(loaded, test_data)

    def test_update_digest(self):
        """ダイジェスト更新（例外なしで成功）"""
        overall = {"digest_type": "test", "keywords": ["a", "b"]}
        # 例外が発生しなければ成功
        self.manager.update_digest("weekly", "W0001_Test", overall)

        data = self.manager.load_or_create()
        self.assertEqual(
            data["major_digests"]["weekly"]["overall_digest"],
            overall
        )

    def test_update_digest_invalid_level(self):
        """無効なレベルへの更新でDigestError"""
        with self.assertRaises(DigestError):
            self.manager.update_digest("invalid", "name", {})


if __name__ == "__main__":
    unittest.main()
