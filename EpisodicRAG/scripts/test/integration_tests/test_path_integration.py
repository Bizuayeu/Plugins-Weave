#!/usr/bin/env python3
"""
Path Integration Tests
======================

パス構造の一貫性を検証する統合テスト。
Provisionalディレクトリが各レベルディレクトリ内に正しく配置されることを確認。
"""

import unittest
from pathlib import Path

from test_helpers import LEVEL_DIRS, TempPluginEnvironment

from application.config import DigestConfig
from domain.constants import LEVEL_CONFIG, LEVEL_NAMES
from domain.file_naming import format_digest_number


class TestProvisionalDirectoryStructure(unittest.TestCase):
    """Provisionalディレクトリ構造のテスト"""

    def test_provisional_dir_is_inside_level_dir(self) -> None:
        """
        get_provisional_dir() がレベルディレクトリ内のパスを返すことを検証

        正しい: Digests/1_Weekly/Provisional/
        間違い: Digests/Provisional/1_Weekly/
        """
        with TempPluginEnvironment() as env:
            config = DigestConfig(plugin_root=env.plugin_root)

            for level in LEVEL_NAMES:
                prov_dir = config.get_provisional_dir(level)
                level_dir = config.get_level_dir(level)

                # Provisionalはレベルディレクトリの直下
                self.assertEqual(prov_dir.parent, level_dir)
                self.assertEqual(prov_dir.name, "Provisional")

    def test_all_level_dirs_have_correct_names(self) -> None:
        """各レベルディレクトリ名がLEVEL_CONFIGと一致することを検証"""
        with TempPluginEnvironment() as env:
            config = DigestConfig(plugin_root=env.plugin_root)

            for level in LEVEL_NAMES:
                level_dir = config.get_level_dir(level)
                expected_name = LEVEL_CONFIG[level]["dir"]

                self.assertEqual(level_dir.name, expected_name)
                self.assertTrue(level_dir.exists())

    def test_provisional_dirs_exist_inside_level_dirs(self) -> None:
        """Provisionalディレクトリがレベルディレクトリ内に存在することを検証"""
        with TempPluginEnvironment() as env:
            config = DigestConfig(plugin_root=env.plugin_root)

            for level in LEVEL_NAMES:
                prov_dir = config.get_provisional_dir(level)
                self.assertTrue(prov_dir.exists())

                # パス構造の検証
                # prov_dir は digests_path / level_dir / "Provisional"
                relative_parts = prov_dir.relative_to(config.digests_path).parts

                # 期待: ("1_Weekly", "Provisional") のような形式
                self.assertEqual(len(relative_parts), 2)
                self.assertEqual(relative_parts[1], "Provisional")


class TestFormatDigestNumber(unittest.TestCase):
    """format_digest_number関数のテスト"""

    def test_format_loop_number(self) -> None:
        """Loop番号のフォーマット検証"""
        self.assertEqual(format_digest_number("loop", 1), "L00001")
        self.assertEqual(format_digest_number("loop", 186), "L00186")
        self.assertEqual(format_digest_number("loop", 9999), "L09999")

    def test_format_weekly_number(self) -> None:
        """Weekly番号のフォーマット検証（4桁）"""
        self.assertEqual(format_digest_number("weekly", 1), "W0001")
        self.assertEqual(format_digest_number("weekly", 123), "W0123")

    def test_format_monthly_number(self) -> None:
        """Monthly番号のフォーマット検証（4桁）"""
        self.assertEqual(format_digest_number("monthly", 1), "M0001")
        self.assertEqual(format_digest_number("monthly", 12), "M0012")

    def test_format_quarterly_number(self) -> None:
        """Quarterly番号のフォーマット検証（3桁）"""
        self.assertEqual(format_digest_number("quarterly", 1), "Q001")

    def test_format_annual_number(self) -> None:
        """Annual番号のフォーマット検証（3桁）"""
        self.assertEqual(format_digest_number("annual", 1), "A001")
        self.assertEqual(format_digest_number("annual", 99), "A099")

    def test_format_multi_decadal_number(self) -> None:
        """Multi-decadal番号のフォーマット検証（MD + 2桁）"""
        self.assertEqual(format_digest_number("multi_decadal", 1), "MD01")
        self.assertEqual(format_digest_number("multi_decadal", 3), "MD03")

    def test_format_centurial_number(self) -> None:
        """Centurial番号のフォーマット検証（2桁）"""
        self.assertEqual(format_digest_number("centurial", 1), "C01")

    def test_invalid_level_raises_error(self) -> None:
        """無効なレベルでConfigErrorが発生することを検証"""
        from domain.exceptions import ConfigError

        with self.assertRaises(ConfigError):
            format_digest_number("invalid_level", 1)

    def test_consistency_with_level_config(self) -> None:
        """LEVEL_CONFIGとの一貫性を検証"""
        for level, cfg in LEVEL_CONFIG.items():
            formatted = format_digest_number(level, 1)
            # プレフィックスが正しいか
            self.assertTrue(formatted.startswith(cfg["prefix"]))
            # 桁数が正しいか（プレフィックス除く）
            number_part = formatted[len(cfg["prefix"]) :]
            self.assertEqual(len(number_part), cfg["digits"])


class TestValidateDirectoryStructure(unittest.TestCase):
    """validate_directory_structure メソッドのテスト"""

    def test_valid_structure_returns_empty_list(self) -> None:
        """正しい構造では空のエラーリストを返す"""
        with TempPluginEnvironment() as env:
            config = DigestConfig(plugin_root=env.plugin_root)
            errors = config.validate_directory_structure()
            self.assertEqual(errors, [])

    def test_missing_loops_detected(self) -> None:
        """Loopsディレクトリが欠落している場合を検出"""
        with TempPluginEnvironment() as env:
            config = DigestConfig(plugin_root=env.plugin_root)
            # Loopsを削除
            import shutil

            shutil.rmtree(env.loops_path)

            errors = config.validate_directory_structure()
            self.assertTrue(any("Loops" in e for e in errors))

    def test_missing_provisional_detected(self) -> None:
        """Provisionalディレクトリが欠落している場合を検出"""
        with TempPluginEnvironment() as env:
            config = DigestConfig(plugin_root=env.plugin_root)
            # 1_Weekly/Provisionalを削除
            import shutil

            shutil.rmtree(env.digests_path / "1_Weekly" / "Provisional")

            errors = config.validate_directory_structure()
            self.assertTrue(any("weekly" in e.lower() and "Provisional" in e for e in errors))


class TestHelperFunctions(unittest.TestCase):
    """test_helpersモジュールの関数テスト"""

    def test_temp_plugin_environment_creates_structure(self) -> None:
        """TempPluginEnvironmentが正しい構造を作成することを検証"""
        with TempPluginEnvironment() as env:
            # 基本ディレクトリの存在確認
            self.assertTrue(env.plugin_root.exists())
            self.assertTrue(env.loops_path.exists())
            self.assertTrue(env.digests_path.exists())
            self.assertTrue(env.essences_path.exists())
            self.assertTrue(env.config_dir.exists())

            # config.jsonの存在確認
            self.assertTrue((env.config_dir / "config.json").exists())

            # 全レベルディレクトリとProvisionalの確認
            for level_dir in LEVEL_DIRS:
                level_path = env.digests_path / level_dir
                self.assertTrue(level_path.exists())
                self.assertTrue((level_path / "Provisional").exists())

    def test_temp_environment_cleanup(self) -> None:
        """一時環境が正しくクリーンアップされることを検証"""
        with TempPluginEnvironment() as env:
            temp_dir = env.plugin_root

        # コンテキスト終了後、ディレクトリは削除されているはず
        self.assertFalse(temp_dir.exists())


if __name__ == "__main__":
    unittest.main()
