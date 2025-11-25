#!/usr/bin/env python3
"""
config.py のユニットテスト
==========================

extract_file_number(), extract_number_only(), DigestConfig クラスのテスト
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    extract_file_number,
    extract_number_only,
    DigestConfig,
    LEVEL_CONFIG,
    LEVEL_NAMES,
)


class TestExtractFileNumber(unittest.TestCase):
    """extract_file_number() のテスト"""

    def test_loop_prefix(self):
        """Loopプレフィックス"""
        self.assertEqual(extract_file_number("Loop0001_タイトル.txt"), ("Loop", 1))
        self.assertEqual(extract_file_number("Loop0186_xxx.txt"), ("Loop", 186))

    def test_weekly_prefix(self):
        """Wプレフィックス（Weekly）"""
        self.assertEqual(extract_file_number("W0001_タイトル.txt"), ("W", 1))
        self.assertEqual(extract_file_number("W0047_xxx.txt"), ("W", 47))

    def test_monthly_prefix(self):
        """Mプレフィックス（Monthly）"""
        self.assertEqual(extract_file_number("M001_タイトル.txt"), ("M", 1))
        self.assertEqual(extract_file_number("M012_xxx.txt"), ("M", 12))

    def test_multi_decadal_prefix(self):
        """MDプレフィックス（Multi-decadal）- 2文字プレフィックスのテスト"""
        self.assertEqual(extract_file_number("MD01_タイトル.txt"), ("MD", 1))
        self.assertEqual(extract_file_number("MD03_xxx.txt"), ("MD", 3))

    def test_other_prefixes(self):
        """その他のプレフィックス（Q, A, T, D, C）"""
        self.assertEqual(extract_file_number("Q001_タイトル.txt"), ("Q", 1))
        self.assertEqual(extract_file_number("A01_タイトル.txt"), ("A", 1))
        self.assertEqual(extract_file_number("T01_タイトル.txt"), ("T", 1))
        self.assertEqual(extract_file_number("D01_タイトル.txt"), ("D", 1))
        self.assertEqual(extract_file_number("C01_タイトル.txt"), ("C", 1))

    def test_invalid_format(self):
        """無効な形式"""
        self.assertIsNone(extract_file_number("invalid.txt"))
        self.assertIsNone(extract_file_number(""))
        self.assertIsNone(extract_file_number("no_number.txt"))


class TestExtractNumberOnly(unittest.TestCase):
    """extract_number_only() のテスト"""

    def test_returns_number(self):
        """番号のみ返す"""
        self.assertEqual(extract_number_only("Loop0001_xxx.txt"), 1)
        self.assertEqual(extract_number_only("MD03_xxx.txt"), 3)

    def test_invalid_returns_none(self):
        """無効な形式はNone"""
        self.assertIsNone(extract_number_only("invalid.txt"))


class TestDigestConfig(unittest.TestCase):
    """DigestConfig クラスのテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリとconfig.jsonを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)

        # .claude-plugin ディレクトリ作成
        self.config_dir = self.plugin_root / ".claude-plugin"
        self.config_dir.mkdir(parents=True)

        # データディレクトリ作成
        self.data_dir = self.plugin_root / "data"
        (self.data_dir / "Loops").mkdir(parents=True)
        (self.data_dir / "Digests").mkdir(parents=True)
        (self.data_dir / "Essences").mkdir(parents=True)

        # config.json 作成
        self.config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4
            }
        }
        self.config_file = self.config_dir / "config.json"
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

    def tearDown(self):
        """一時ディレクトリを削除"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_explicit_plugin_root(self):
        """明示的なplugin_rootで初期化"""
        config = DigestConfig(plugin_root=self.plugin_root)
        self.assertEqual(config.plugin_root, self.plugin_root)
        self.assertEqual(config.config_file, self.config_file)

    def test_load_config_success(self):
        """設定ファイルの読み込み成功"""
        config = DigestConfig(plugin_root=self.plugin_root)
        self.assertEqual(config.config["base_dir"], ".")
        self.assertIn("paths", config.config)
        self.assertIn("levels", config.config)

    def test_load_config_not_found(self):
        """設定ファイルが見つからない場合"""
        # config.jsonを削除
        self.config_file.unlink()
        with self.assertRaises(FileNotFoundError):
            DigestConfig(plugin_root=self.plugin_root)

    def test_load_config_invalid_json(self):
        """無効なJSONの場合"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("invalid json {")
        with self.assertRaises(json.JSONDecodeError):
            DigestConfig(plugin_root=self.plugin_root)

    def test_resolve_base_dir_dot(self):
        """base_dir="." の場合はplugin_rootと同じ"""
        config = DigestConfig(plugin_root=self.plugin_root)
        self.assertEqual(config.base_dir, self.plugin_root.resolve())

    def test_resolve_base_dir_relative(self):
        """相対パスのbase_dir"""
        # base_dirを変更
        self.config_data["base_dir"] = "data"
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

        config = DigestConfig(plugin_root=self.plugin_root)
        self.assertEqual(config.base_dir, (self.plugin_root / "data").resolve())

    def test_loops_path(self):
        """loops_pathプロパティ"""
        config = DigestConfig(plugin_root=self.plugin_root)
        expected = (self.plugin_root / "data" / "Loops").resolve()
        self.assertEqual(config.loops_path, expected)

    def test_digests_path(self):
        """digests_pathプロパティ"""
        config = DigestConfig(plugin_root=self.plugin_root)
        expected = (self.plugin_root / "data" / "Digests").resolve()
        self.assertEqual(config.digests_path, expected)

    def test_essences_path(self):
        """essences_pathプロパティ"""
        config = DigestConfig(plugin_root=self.plugin_root)
        expected = (self.plugin_root / "data" / "Essences").resolve()
        self.assertEqual(config.essences_path, expected)

    def test_resolve_path_missing_key(self):
        """存在しないキーの場合"""
        config = DigestConfig(plugin_root=self.plugin_root)
        with self.assertRaises(KeyError):
            config.resolve_path("nonexistent_key")

    def test_resolve_path_missing_paths_section(self):
        """pathsセクションがない場合"""
        del self.config_data["paths"]
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

        config = DigestConfig(plugin_root=self.plugin_root)
        with self.assertRaises(KeyError):
            config.resolve_path("loops_dir")

    def test_get_level_dir_all_levels(self):
        """全レベルのディレクトリ取得"""
        config = DigestConfig(plugin_root=self.plugin_root)
        for level in LEVEL_NAMES:
            level_dir = config.get_level_dir(level)
            expected_subdir = LEVEL_CONFIG[level]["dir"]
            self.assertTrue(str(level_dir).endswith(expected_subdir))

    def test_get_level_dir_invalid_level(self):
        """無効なレベル名の場合"""
        config = DigestConfig(plugin_root=self.plugin_root)
        with self.assertRaises(ValueError):
            config.get_level_dir("invalid_level")

    def test_get_provisional_dir_all_levels(self):
        """全レベルのProvisionalディレクトリ取得"""
        config = DigestConfig(plugin_root=self.plugin_root)
        for level in LEVEL_NAMES:
            prov_dir = config.get_provisional_dir(level)
            self.assertTrue(str(prov_dir).endswith("Provisional"))

    def test_threshold_properties_all_levels(self):
        """全レベルのthresholdプロパティ"""
        config = DigestConfig(plugin_root=self.plugin_root)

        # 設定ファイルの値と一致することを確認
        self.assertEqual(config.weekly_threshold, 5)
        self.assertEqual(config.monthly_threshold, 5)
        self.assertEqual(config.quarterly_threshold, 3)
        self.assertEqual(config.annual_threshold, 4)
        self.assertEqual(config.triennial_threshold, 3)
        self.assertEqual(config.decadal_threshold, 3)
        self.assertEqual(config.multi_decadal_threshold, 3)
        self.assertEqual(config.centurial_threshold, 4)

    def test_threshold_properties_default_values(self):
        """thresholdのデフォルト値"""
        # levelsセクションを削除
        del self.config_data["levels"]
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

        config = DigestConfig(plugin_root=self.plugin_root)

        # デフォルト値が返されることを確認
        self.assertEqual(config.weekly_threshold, 5)
        self.assertEqual(config.monthly_threshold, 5)
        self.assertEqual(config.quarterly_threshold, 3)
        self.assertEqual(config.annual_threshold, 4)
        self.assertEqual(config.triennial_threshold, 3)
        self.assertEqual(config.decadal_threshold, 3)
        self.assertEqual(config.multi_decadal_threshold, 3)
        self.assertEqual(config.centurial_threshold, 4)

    def test_threshold_properties_custom_values(self):
        """カスタムthreshold値"""
        self.config_data["levels"]["weekly_threshold"] = 10
        self.config_data["levels"]["monthly_threshold"] = 8
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

        config = DigestConfig(plugin_root=self.plugin_root)
        self.assertEqual(config.weekly_threshold, 10)
        self.assertEqual(config.monthly_threshold, 8)

    def test_get_identity_file_path_none(self):
        """identity_file_pathがNoneの場合"""
        config = DigestConfig(plugin_root=self.plugin_root)
        self.assertIsNone(config.get_identity_file_path())

    def test_get_identity_file_path_configured(self):
        """identity_file_pathが設定されている場合"""
        self.config_data["paths"]["identity_file_path"] = "Identity.md"
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

        config = DigestConfig(plugin_root=self.plugin_root)
        identity_path = config.get_identity_file_path()
        self.assertIsNotNone(identity_path)
        self.assertTrue(str(identity_path).endswith("Identity.md"))

    # ===== get_threshold() メソッドのテスト =====

    def test_get_threshold_all_levels(self):
        """get_threshold()が全レベルで正しい値を返す"""
        config = DigestConfig(plugin_root=self.plugin_root)

        # 設定ファイルの値と一致することを確認
        self.assertEqual(config.get_threshold("weekly"), 5)
        self.assertEqual(config.get_threshold("monthly"), 5)
        self.assertEqual(config.get_threshold("quarterly"), 3)
        self.assertEqual(config.get_threshold("annual"), 4)
        self.assertEqual(config.get_threshold("triennial"), 3)
        self.assertEqual(config.get_threshold("decadal"), 3)
        self.assertEqual(config.get_threshold("multi_decadal"), 3)
        self.assertEqual(config.get_threshold("centurial"), 4)

    def test_get_threshold_invalid_level(self):
        """get_threshold()が無効なレベルでValueErrorを発生させる"""
        config = DigestConfig(plugin_root=self.plugin_root)
        with self.assertRaises(ValueError):
            config.get_threshold("invalid_level")

    def test_get_threshold_default_values(self):
        """get_threshold()がlevelsセクションがない場合もデフォルト値を返す"""
        del self.config_data["levels"]
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

        config = DigestConfig(plugin_root=self.plugin_root)
        self.assertEqual(config.get_threshold("weekly"), 5)
        self.assertEqual(config.get_threshold("quarterly"), 3)
        self.assertEqual(config.get_threshold("annual"), 4)

    def test_get_threshold_custom_values(self):
        """get_threshold()がカスタム値を正しく返す"""
        self.config_data["levels"]["weekly_threshold"] = 10
        self.config_data["levels"]["monthly_threshold"] = 8
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

        config = DigestConfig(plugin_root=self.plugin_root)
        self.assertEqual(config.get_threshold("weekly"), 10)
        self.assertEqual(config.get_threshold("monthly"), 8)

    def test_get_threshold_matches_properties(self):
        """get_threshold()と既存プロパティが同じ値を返す"""
        config = DigestConfig(plugin_root=self.plugin_root)

        # 全レベルでプロパティとget_threshold()が一致することを確認
        self.assertEqual(config.get_threshold("weekly"), config.weekly_threshold)
        self.assertEqual(config.get_threshold("monthly"), config.monthly_threshold)
        self.assertEqual(config.get_threshold("quarterly"), config.quarterly_threshold)
        self.assertEqual(config.get_threshold("annual"), config.annual_threshold)
        self.assertEqual(config.get_threshold("triennial"), config.triennial_threshold)
        self.assertEqual(config.get_threshold("decadal"), config.decadal_threshold)
        self.assertEqual(config.get_threshold("multi_decadal"), config.multi_decadal_threshold)
        self.assertEqual(config.get_threshold("centurial"), config.centurial_threshold)


class TestLevelConfig(unittest.TestCase):
    """LEVEL_CONFIG 定数のテスト"""

    def test_all_levels_have_required_keys(self):
        """全レベルに必要なキーが存在"""
        required_keys = {"prefix", "digits", "dir", "source", "next"}
        for level, config in LEVEL_CONFIG.items():
            for key in required_keys:
                self.assertIn(key, config, f"Level '{level}' missing key '{key}'")

    def test_level_names_matches_config_keys(self):
        """LEVEL_NAMESとLEVEL_CONFIGのキーが一致"""
        self.assertEqual(set(LEVEL_NAMES), set(LEVEL_CONFIG.keys()))

    def test_level_chain_is_valid(self):
        """レベルチェーンが有効（nextが正しく設定されている）"""
        for level, config in LEVEL_CONFIG.items():
            next_level = config["next"]
            if next_level is not None:
                self.assertIn(next_level, LEVEL_CONFIG,
                              f"Level '{level}' has invalid next: '{next_level}'")


if __name__ == "__main__":
    unittest.main()
