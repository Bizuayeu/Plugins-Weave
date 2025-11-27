#!/usr/bin/env python3
"""
config.py のユニットテスト
==========================

extract_file_number(), extract_number_only(), DigestConfig クラスのテスト

Note:
    pytestとunittestの両方で実行可能。
    pytest実行時はpytest.mark.unitマーカーを使用。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    extract_file_number,
    extract_number_only,
    DigestConfig,
    LEVEL_CONFIG,
    LEVEL_NAMES,
)
from domain.exceptions import ConfigError


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
        with self.assertRaises(ConfigError):
            DigestConfig(plugin_root=self.plugin_root)

    def test_load_config_invalid_json(self):
        """無効なJSONの場合"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            f.write("invalid json {")
        with self.assertRaises(ConfigError):
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
        with self.assertRaises(ConfigError):
            config.resolve_path("nonexistent_key")

    def test_resolve_path_missing_paths_section(self):
        """pathsセクションがない場合"""
        del self.config_data["paths"]
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config_data, f)

        config = DigestConfig(plugin_root=self.plugin_root)
        with self.assertRaises(ConfigError):
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
        """get_threshold()が無効なレベルでConfigErrorを発生させる"""
        config = DigestConfig(plugin_root=self.plugin_root)
        with self.assertRaises(ConfigError):
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


# =============================================================================
# エッジケーステスト（Phase 0で追加）
# =============================================================================

from config import format_digest_number


class TestExtractFileNumberEdgeCases(unittest.TestCase):
    """extract_file_number() のエッジケーステスト"""

    def test_non_string_input_returns_none(self):
        """非文字列型入力はNoneを返す"""
        self.assertIsNone(extract_file_number(None))
        self.assertIsNone(extract_file_number(123))
        self.assertIsNone(extract_file_number(['Loop0001']))
        self.assertIsNone(extract_file_number({'name': 'Loop0001'}))

    def test_unicode_special_chars(self):
        """Unicode特殊文字を含むファイル名"""
        self.assertEqual(extract_file_number("Loop0001_日本語タイトル.txt"), ("Loop", 1))
        self.assertEqual(extract_file_number("W0001_絵文字🎉.txt"), ("W", 1))

    def test_very_long_filename(self):
        """極端に長いファイル名"""
        long_title = "a" * 1000
        self.assertEqual(extract_file_number(f"Loop0001_{long_title}.txt"), ("Loop", 1))

    def test_number_overflow(self):
        """大きな番号"""
        self.assertEqual(extract_file_number("Loop99999999.txt"), ("Loop", 99999999))

    def test_leading_zeros(self):
        """先頭ゼロのバリエーション"""
        self.assertEqual(extract_file_number("Loop0000.txt"), ("Loop", 0))
        self.assertEqual(extract_file_number("W00001.txt"), ("W", 1))

    def test_empty_string(self):
        """空文字列"""
        self.assertIsNone(extract_file_number(""))

    def test_only_prefix_no_number(self):
        """プレフィックスのみで番号なし"""
        self.assertIsNone(extract_file_number("Loop.txt"))
        self.assertIsNone(extract_file_number("W_title.txt"))

    def test_number_only_no_prefix(self):
        """番号のみでプレフィックスなし"""
        self.assertIsNone(extract_file_number("0001.txt"))
        self.assertIsNone(extract_file_number("12345.txt"))


class TestFormatDigestNumberEdgeCases(unittest.TestCase):
    """format_digest_number() のエッジケーステスト"""

    def test_zero_number(self):
        """番号0の処理"""
        self.assertEqual(format_digest_number("loop", 0), "Loop0000")
        self.assertEqual(format_digest_number("weekly", 0), "W0000")

    def test_very_large_number(self):
        """桁数を超える大きな番号"""
        # 4桁を超える場合でも動作する（桁数は最小桁数）
        result = format_digest_number("weekly", 99999)
        self.assertEqual(result, "W99999")

    def test_invalid_level_raises_valueerror(self):
        """無効なレベル名でValueError"""
        with self.assertRaises(ValueError):
            format_digest_number("invalid_level", 1)

    def test_all_valid_levels(self):
        """すべての有効なレベルで正しく動作"""
        expected = {
            "loop": "Loop0001",
            "weekly": "W0001",
            "monthly": "M001",
            "quarterly": "Q001",
            "annual": "A01",
            "triennial": "T01",
            "decadal": "D01",
            "multi_decadal": "MD01",
            "centurial": "C01",
        }
        for level, expected_result in expected.items():
            result = format_digest_number(level, 1)
            self.assertEqual(result, expected_result, f"Failed for level '{level}'")


class TestExtractNumberOnlyEdgeCases(unittest.TestCase):
    """extract_number_only() のエッジケーステスト"""

    def test_non_string_returns_none(self):
        """非文字列型入力はNoneを返す"""
        self.assertIsNone(extract_number_only(None))
        self.assertIsNone(extract_number_only(123))

    def test_zero_number(self):
        """番号0の抽出"""
        self.assertEqual(extract_number_only("Loop0000.txt"), 0)


# =============================================================================
# validate_directory_structure() テスト（Phase 0で追加）
# =============================================================================


class TestValidateDirectoryStructure(unittest.TestCase):
    """validate_directory_structure() のテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリとconfig.jsonを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)

        # .claude-plugin ディレクトリ作成
        self.config_dir = self.plugin_root / ".claude-plugin"
        self.config_dir.mkdir(parents=True)

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

    def _create_full_directory_structure(self):
        """完全なディレクトリ構造を作成"""
        data_dir = self.plugin_root / "data"
        (data_dir / "Loops").mkdir(parents=True, exist_ok=True)
        (data_dir / "Digests").mkdir(parents=True, exist_ok=True)
        (data_dir / "Essences").mkdir(parents=True, exist_ok=True)

        # 各レベルディレクトリとProvisionalを作成
        for level in LEVEL_NAMES:
            level_subdir = LEVEL_CONFIG[level]["dir"]
            level_dir = data_dir / "Digests" / level_subdir
            level_dir.mkdir(parents=True, exist_ok=True)
            (level_dir / "Provisional").mkdir(exist_ok=True)

    def test_validate_directory_structure_all_present(self):
        """全ディレクトリ存在時はエラーなし"""
        self._create_full_directory_structure()
        config = DigestConfig(plugin_root=self.plugin_root)
        errors = config.validate_directory_structure()
        self.assertEqual(errors, [])

    def test_validate_directory_structure_missing_loops(self):
        """Loopsディレクトリ欠落"""
        self._create_full_directory_structure()
        # Loopsを削除
        import shutil
        shutil.rmtree(self.plugin_root / "data" / "Loops")

        config = DigestConfig(plugin_root=self.plugin_root)
        errors = config.validate_directory_structure()

        self.assertEqual(len(errors), 1)
        self.assertIn("Loops", errors[0])

    def test_validate_directory_structure_missing_digests(self):
        """Digestsディレクトリ欠落"""
        data_dir = self.plugin_root / "data"
        (data_dir / "Loops").mkdir(parents=True, exist_ok=True)
        (data_dir / "Essences").mkdir(parents=True, exist_ok=True)
        # Digestsを作成しない

        config = DigestConfig(plugin_root=self.plugin_root)
        errors = config.validate_directory_structure()

        # Digestsが無いので、Digests自体 + 全レベルディレクトリのエラー
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Digests" in e for e in errors))

    def test_validate_directory_structure_missing_essences(self):
        """Essencesディレクトリ欠落"""
        self._create_full_directory_structure()
        # Essencesを削除
        import shutil
        shutil.rmtree(self.plugin_root / "data" / "Essences")

        config = DigestConfig(plugin_root=self.plugin_root)
        errors = config.validate_directory_structure()

        self.assertEqual(len(errors), 1)
        self.assertIn("Essences", errors[0])

    def test_validate_directory_structure_missing_level_dir(self):
        """レベルディレクトリ（1_Weekly等）欠落"""
        self._create_full_directory_structure()
        # 1_Weeklyを削除
        import shutil
        weekly_dir = self.plugin_root / "data" / "Digests" / "1_Weekly"
        shutil.rmtree(weekly_dir)

        config = DigestConfig(plugin_root=self.plugin_root)
        errors = config.validate_directory_structure()

        self.assertEqual(len(errors), 1)
        self.assertIn("weekly", errors[0].lower())

    def test_validate_directory_structure_missing_provisional(self):
        """Provisionalディレクトリ欠落"""
        self._create_full_directory_structure()
        # 1_Weekly/Provisionalを削除
        import shutil
        prov_dir = self.plugin_root / "data" / "Digests" / "1_Weekly" / "Provisional"
        shutil.rmtree(prov_dir)

        config = DigestConfig(plugin_root=self.plugin_root)
        errors = config.validate_directory_structure()

        self.assertEqual(len(errors), 1)
        self.assertIn("Provisional", errors[0])

    def test_validate_directory_structure_multiple_errors(self):
        """複数エラーの集約"""
        data_dir = self.plugin_root / "data"
        # Loopsのみ作成（Digests, Essencesなし）
        (data_dir / "Loops").mkdir(parents=True, exist_ok=True)

        config = DigestConfig(plugin_root=self.plugin_root)
        errors = config.validate_directory_structure()

        # Digests, Essences, + 全レベルディレクトリのエラー
        self.assertGreater(len(errors), 2)
        self.assertTrue(any("Digests" in e for e in errors))
        self.assertTrue(any("Essences" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
