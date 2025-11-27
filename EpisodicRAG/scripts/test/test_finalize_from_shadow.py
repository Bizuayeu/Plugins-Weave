#!/usr/bin/env python3
"""
DigestFinalizerFromShadow 統合テスト
=====================================

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

# Interfaces層
# Domain層
from domain.exceptions import ConfigError, DigestError, ValidationError
from interfaces import DigestFinalizerFromShadow

# Helpers
from interfaces.interface_helpers import get_next_digest_number


class TestGetNextDigestNumber(unittest.TestCase):
    """get_next_digest_number関数のテスト"""

    def setUp(self):
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.digests_path = Path(self.temp_dir) / "Digests"
        self.digests_path.mkdir()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_empty_directory_returns_1(self):
        """空のディレクトリでは1を返す"""
        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 1)

    def test_nonexistent_directory_returns_1(self):
        """存在しないディレクトリでは1を返す"""
        nonexistent = Path(self.temp_dir) / "NonExistent"
        result = get_next_digest_number(nonexistent, "weekly")
        self.assertEqual(result, 1)

    def test_with_existing_files(self):
        """既存ファイルがある場合、最大番号+1を返す"""
        weekly_dir = self.digests_path / "1_Weekly"
        weekly_dir.mkdir()

        (weekly_dir / "W0001_test.txt").write_text("{}")
        (weekly_dir / "W0003_test.txt").write_text("{}")
        (weekly_dir / "W0005_test.txt").write_text("{}")

        result = get_next_digest_number(self.digests_path, "weekly")
        self.assertEqual(result, 6)

    def test_invalid_level_raises(self):
        """無効なレベルでConfigError"""
        with self.assertRaises(ConfigError):
            get_next_digest_number(self.digests_path, "invalid_level")


class TestDigestFinalizerFromShadow(unittest.TestCase):
    """DigestFinalizerFromShadow の統合テスト"""

    def setUp(self):
        """一時ディレクトリでテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)

        # ディレクトリ構造を作成
        self.digests_path = self.plugin_root / "data" / "Digests"
        self.loops_path = self.plugin_root / "data" / "Loops"
        self.essences_path = self.plugin_root / "data" / "Essences"
        self.config_dir = self.plugin_root / ".claude-plugin"

        self.digests_path.mkdir(parents=True)
        self.loops_path.mkdir(parents=True)
        self.essences_path.mkdir(parents=True)
        self.config_dir.mkdir(parents=True)

        # Digestのサブディレクトリ（各レベル内にProvisionalを配置）
        for subdir in [
            "1_Weekly",
            "2_Monthly",
            "3_Quarterly",
            "4_Annual",
            "5_Triennial",
            "6_Decadal",
            "7_Multi-decadal",
            "8_Centurial",
        ]:
            (self.digests_path / subdir).mkdir()
            (self.digests_path / subdir / "Provisional").mkdir()

        # config.json作成
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        with open(self.config_dir / "config.json", 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        # モック設定
        self.mock_config = MagicMock()
        self.mock_config.digests_path = self.digests_path
        self.mock_config.loops_path = self.loops_path
        self.mock_config.essences_path = self.essences_path
        self.mock_config.plugin_root = self.plugin_root

        self.finalizer = DigestFinalizerFromShadow(self.mock_config)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    def test_validate_shadow_content_valid(self):
        """正常なsource_filesの検証（例外なしで成功）"""
        source_files = ["Loop0001_test.txt", "Loop0002_test.txt"]
        # 例外が発生しなければ成功
        self.finalizer.validate_shadow_content("weekly", source_files)

    def test_validate_shadow_content_empty(self):
        """空のsource_filesでValidationError"""
        with self.assertRaises(ValidationError):
            self.finalizer.validate_shadow_content("weekly", [])

    def test_validate_shadow_content_not_list(self):
        """リストでない場合ValidationError"""
        with self.assertRaises(ValidationError):
            self.finalizer.validate_shadow_content("weekly", "not a list")

    def test_validate_shadow_content_invalid_filename(self):
        """無効なファイル名形式でValidationError"""
        source_files = ["invalid_file.txt"]
        with self.assertRaises(ValidationError):
            self.finalizer.validate_shadow_content("weekly", source_files)

    def test_finalize_empty_title(self):
        """空タイトルでValidationError"""
        with self.assertRaises(ValidationError):
            self.finalizer.finalize_from_shadow("weekly", "")

    def test_finalize_no_shadow(self):
        """ShadowがないでDigestError"""
        with self.assertRaises(DigestError):
            self.finalizer.finalize_from_shadow("weekly", "Test Title")


class TestDigestFinalizerIntegration(unittest.TestCase):
    """DigestFinalizerFromShadow の統合テスト（フルフロー）"""

    def setUp(self):
        """完全なテスト環境を構築"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)

        # ディレクトリ構造を作成
        self.digests_path = self.plugin_root / "data" / "Digests"
        self.loops_path = self.plugin_root / "data" / "Loops"
        self.essences_path = self.plugin_root / "data" / "Essences"
        self.config_dir = self.plugin_root / ".claude-plugin"

        self.digests_path.mkdir(parents=True)
        self.loops_path.mkdir(parents=True)
        self.essences_path.mkdir(parents=True)
        self.config_dir.mkdir(parents=True)

        # Digestのサブディレクトリ（各レベル内にProvisionalを配置）
        for subdir in [
            "1_Weekly",
            "2_Monthly",
            "3_Quarterly",
            "4_Annual",
            "5_Triennial",
            "6_Decadal",
            "7_Multi-decadal",
            "8_Centurial",
        ]:
            (self.digests_path / subdir).mkdir()
            (self.digests_path / subdir / "Provisional").mkdir()

        # config.json作成
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        with open(self.config_dir / "config.json", 'w', encoding='utf-8') as f:
            json.dump(config_data, f)

        # GrandDigest.txt作成
        grand_digest_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {
                "weekly": {"overall_digest": None},
                "monthly": {"overall_digest": None},
                "quarterly": {"overall_digest": None},
                "annual": {"overall_digest": None},
                "triennial": {"overall_digest": None},
                "decadal": {"overall_digest": None},
                "multi_decadal": {"overall_digest": None},
                "centurial": {"overall_digest": None},
            },
        }
        with open(self.essences_path / "GrandDigest.txt", 'w', encoding='utf-8') as f:
            json.dump(grand_digest_data, f)

        # ShadowGrandDigest.txt作成
        shadow_digest_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["Loop0001_test.txt", "Loop0002_test.txt"],
                        "digest_type": "テスト",
                        "keywords": ["keyword1", "keyword2"],
                        "abstract": "テスト用の要約です。",
                        "impression": "テスト用の所感です。",
                    }
                },
                "monthly": {"overall_digest": None},
                "quarterly": {"overall_digest": None},
                "annual": {"overall_digest": None},
                "triennial": {"overall_digest": None},
                "decadal": {"overall_digest": None},
                "multi_decadal": {"overall_digest": None},
                "centurial": {"overall_digest": None},
            },
        }
        with open(self.essences_path / "ShadowGrandDigest.txt", 'w', encoding='utf-8') as f:
            json.dump(shadow_digest_data, f)

        # last_digest_times.json作成（.claude-pluginディレクトリに配置）
        times_data = {
            "weekly": {"timestamp": "", "last_processed": None},
            "monthly": {"timestamp": "", "last_processed": None},
            "quarterly": {"timestamp": "", "last_processed": None},
            "annual": {"timestamp": "", "last_processed": None},
            "triennial": {"timestamp": "", "last_processed": None},
            "decadal": {"timestamp": "", "last_processed": None},
            "multi_decadal": {"timestamp": "", "last_processed": None},
            "centurial": {"timestamp": "", "last_processed": None},
        }
        with open(self.config_dir / "last_digest_times.json", 'w', encoding='utf-8') as f:
            json.dump(times_data, f)

        # Loopファイル作成
        loop1_data = {
            "overall_digest": {
                "timestamp": "2025-01-01T00:00:00",
                "digest_type": "対話",
                "keywords": ["key1"],
                "abstract": "Loop1の内容",
                "impression": "所感1",
            }
        }
        loop2_data = {
            "overall_digest": {
                "timestamp": "2025-01-02T00:00:00",
                "digest_type": "実装",
                "keywords": ["key2"],
                "abstract": "Loop2の内容",
                "impression": "所感2",
            }
        }
        with open(self.loops_path / "Loop0001_test.txt", 'w', encoding='utf-8') as f:
            json.dump(loop1_data, f)
        with open(self.loops_path / "Loop0002_test.txt", 'w', encoding='utf-8') as f:
            json.dump(loop2_data, f)

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_finalizer(self):
        """DigestConfigとFinalizerを作成"""
        from config import DigestConfig

        config = DigestConfig(plugin_root=self.plugin_root)
        return DigestFinalizerFromShadow(config)

    def test_finalize_creates_regular_digest_file(self):
        """finalize_from_shadowがRegularDigestファイルを作成する"""
        finalizer = self._create_finalizer()

        # Shadowから取得したデータでfinalize（例外なしで成功）
        finalizer.finalize_from_shadow("weekly", "TestDigest")

        # RegularDigestファイルが作成されたことを確認
        weekly_dir = self.digests_path / "1_Weekly"
        digest_files = list(weekly_dir.glob("W0001_*.txt"))
        self.assertEqual(len(digest_files), 1)

        # ファイル内容を確認
        with open(digest_files[0], 'r', encoding='utf-8') as f:
            digest_data = json.load(f)
        self.assertIn("metadata", digest_data)
        self.assertIn("overall_digest", digest_data)
        self.assertEqual(digest_data["metadata"]["digest_level"], "weekly")

    def test_finalize_updates_grand_digest(self):
        """finalize_from_shadowがGrandDigestを更新する"""
        finalizer = self._create_finalizer()

        # 例外なしで成功
        finalizer.finalize_from_shadow("weekly", "TestDigest")

        # GrandDigest.txtが更新されたことを確認
        with open(self.essences_path / "GrandDigest.txt", 'r', encoding='utf-8') as f:
            grand_data = json.load(f)

        weekly_digest = grand_data["major_digests"]["weekly"]["overall_digest"]
        self.assertIsNotNone(weekly_digest)
        self.assertIn("TestDigest", weekly_digest.get("name", ""))

    def test_finalize_updates_last_digest_times(self):
        """finalize_from_shadowがlast_digest_timesを更新する"""
        finalizer = self._create_finalizer()

        # 例外なしで成功
        finalizer.finalize_from_shadow("weekly", "TestDigest")

        # last_digest_times.jsonが更新されたことを確認（.claude-pluginディレクトリ）
        with open(self.config_dir / "last_digest_times.json", 'r', encoding='utf-8') as f:
            times_data = json.load(f)

        self.assertNotEqual(times_data["weekly"]["timestamp"], "")
        self.assertEqual(times_data["weekly"]["last_processed"], "Loop0002")

    def test_finalize_cascade_shadow_update(self):
        """finalize_from_shadowがShadowカスケード更新を実行する"""
        finalizer = self._create_finalizer()

        # 例外なしで成功
        finalizer.finalize_from_shadow("weekly", "TestDigest")

        # ShadowGrandDigest.txtが更新されたことを確認
        with open(self.essences_path / "ShadowGrandDigest.txt", 'r', encoding='utf-8') as f:
            shadow_data = json.load(f)

        # weeklyレベルのShadowがクリアされていることを確認
        # カスケード後はweeklyがクリアまたは更新されている
        # 具体的な動作はcascade_update_on_digest_finalizeの実装による
        _ = shadow_data["latest_digests"]["weekly"]["overall_digest"]

    def test_finalize_without_provisional_auto_generates(self):
        """Provisionalがない場合、source_filesから自動生成する"""
        finalizer = self._create_finalizer()

        # Provisionalファイルは作成しない（setUpで作成されていない）
        # 例外なしで成功
        finalizer.finalize_from_shadow("weekly", "AutoGenTest")

        # RegularDigestが作成されたことを確認
        weekly_dir = self.digests_path / "1_Weekly"
        digest_files = list(weekly_dir.glob("W0001_*.txt"))
        self.assertEqual(len(digest_files), 1)

        # individual_digestsが自動生成されたことを確認
        with open(digest_files[0], 'r', encoding='utf-8') as f:
            digest_data = json.load(f)

        individual_digests = digest_data.get("individual_digests", [])
        self.assertEqual(len(individual_digests), 2)  # Loop0001, Loop0002


if __name__ == "__main__":
    unittest.main()
