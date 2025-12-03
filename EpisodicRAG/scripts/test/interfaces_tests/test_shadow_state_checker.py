#!/usr/bin/env python3
"""
shadow_state_checker.py のテスト
================================

ShadowStateChecker クラスと CLI エントリーポイントのテスト。
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest


class TestShadowStateChecker(unittest.TestCase):
    """ShadowStateChecker クラスのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self) -> None:

        """プラグイン構造を作成"""
        # ディレクトリ構造
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        # config.json
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
            },
        }
        with open(
            self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8"
        ) as f:
            json.dump(config_data, f)

    def _create_shadow_with_placeholders(self) -> None:

        """プレースホルダー付きのShadowGrandDigestを作成"""
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001", "L00002"],
                        "digest_type": "<!-- PLACEHOLDER -->",
                        "keywords": [],
                        "abstract": "<!-- PLACEHOLDER -->",
                        "impression": "<!-- PLACEHOLDER -->",
                    }
                },
            },
        }
        with open(
            self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(shadow_data, f)

    def _create_shadow_analyzed(self) -> None:

        """分析済みのShadowGrandDigestを作成"""
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001", "L00002", "L00003"],
                        "digest_type": "テスト分析",
                        "keywords": ["キーワード1", "キーワード2"],
                        "abstract": "これは分析済みの要約です。",
                        "impression": "これは分析済みの所感です。",
                    }
                },
            },
        }
        with open(
            self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(shadow_data, f)

    def _create_shadow_empty_level(self) -> None:

        """空のレベルを持つShadowGrandDigestを作成"""
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {},
                "monthly": {
                    "overall_digest": {
                        "source_files": [],
                        "digest_type": None,
                        "keywords": None,
                        "abstract": None,
                        "impression": None,
                    }
                },
            },
        }
        with open(
            self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(shadow_data, f)

    @pytest.mark.unit
    def test_check_returns_analyzed_true_when_no_placeholders(self) -> None:

        """プレースホルダーなしの場合analyzed=Trueを返す"""
        # Import here to avoid path issues
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.shadow_state_checker import ShadowStateChecker

        self._create_shadow_analyzed()
        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertEqual(result.status, "ok")
        self.assertTrue(result.analyzed)
        self.assertEqual(result.source_count, 3)
        self.assertEqual(result.placeholder_fields, [])
        self.assertIn("All fields analyzed", result.message)

    @pytest.mark.unit
    def test_check_returns_analyzed_false_when_placeholders_exist(self) -> None:

        """プレースホルダーありの場合analyzed=Falseを返す"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.shadow_state_checker import ShadowStateChecker

        self._create_shadow_with_placeholders()
        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertEqual(result.status, "ok")
        self.assertFalse(result.analyzed)
        self.assertEqual(result.source_count, 2)
        self.assertIn("abstract", result.placeholder_fields)
        self.assertIn("impression", result.placeholder_fields)
        self.assertIn("Placeholders detected", result.message)

    @pytest.mark.unit
    def test_check_returns_ok_for_empty_level(self) -> None:

        """空のレベルの場合も正常に処理"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.shadow_state_checker import ShadowStateChecker

        self._create_shadow_empty_level()
        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertEqual(result.status, "ok")
        self.assertTrue(result.analyzed)
        self.assertEqual(result.source_count, 0)

    @pytest.mark.unit
    def test_check_returns_error_for_invalid_level(self) -> None:

        """無効なレベルの場合エラーを返す"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.shadow_state_checker import ShadowStateChecker

        self._create_shadow_analyzed()
        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        result = checker.check("invalid_level")

        self.assertEqual(result.status, "error")
        self.assertFalse(result.analyzed)
        self.assertIn("Invalid level", result.error)

    @pytest.mark.unit
    def test_check_returns_error_when_config_missing(self) -> None:

        """設定ファイル不在の場合エラーを返す"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.shadow_state_checker import ShadowStateChecker

        # config.jsonを削除
        (self.plugin_root / ".claude-plugin" / "config.json").unlink()

        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertEqual(result.status, "error")
        self.assertFalse(result.analyzed)
        self.assertIn("config.json", result.error)

    @pytest.mark.unit
    def test_check_returns_error_when_shadow_missing(self) -> None:

        """ShadowGrandDigest不在の場合エラーを返す"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.shadow_state_checker import ShadowStateChecker

        # ShadowGrandDigest.txtを作成しない
        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertEqual(result.status, "error")
        self.assertFalse(result.analyzed)
        self.assertIn("ShadowGrandDigest.txt", result.error)

    @pytest.mark.unit
    def test_check_detects_null_fields_as_placeholders(self) -> None:

        """nullフィールドをプレースホルダーとして検出"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.shadow_state_checker import ShadowStateChecker

        self._create_shadow_empty_level()
        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        result = checker.check("monthly")

        self.assertEqual(result.status, "ok")
        self.assertFalse(result.analyzed)
        # nullフィールドがプレースホルダーとして検出される
        self.assertIn("abstract", result.placeholder_fields)


class TestShadowStateCheckerGetEssencesPath(unittest.TestCase):
    """ShadowStateChecker _get_essences_path メソッドのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_get_essences_path_with_relative_base_dir(self) -> None:

        """相対パスのbase_dir（'.'）を解決する"""
        from interfaces.shadow_state_checker import ShadowStateChecker

        # config.jsonを作成（base_dir='.'）
        config_data = {
            "base_dir": ".",
            "paths": {"essences_dir": "data/Essences"},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        config = checker._load_config()
        result = checker._get_essences_path(config)

        # '.'の場合、plugin_rootを基準に解決される
        assert result.is_absolute()
        assert str(self.plugin_root) in str(result)
        assert "Essences" in str(result)

    @pytest.mark.unit
    def test_get_essences_path_with_absolute_base_dir(self) -> None:

        """絶対パスのbase_dirをそのまま使用する"""
        from interfaces.shadow_state_checker import ShadowStateChecker

        # config.jsonを作成（絶対パス）
        abs_path = str(self.plugin_root / "absolute" / "path")
        config_data = {
            "base_dir": abs_path,
            "paths": {"essences_dir": "data/Essences"},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        config = checker._load_config()
        result = checker._get_essences_path(config)

        # 絶対パスはそのまま使用
        assert result.is_absolute()
        assert "Essences" in str(result)

    @pytest.mark.unit
    def test_get_essences_path_with_tilde_base_dir(self) -> None:

        """チルダ(~)を含むbase_dirを展開する"""
        from interfaces.shadow_state_checker import ShadowStateChecker

        # config.jsonを作成（チルダパス）
        config_data = {
            "base_dir": "~/test/path",
            "paths": {"essences_dir": "data/Essences"},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        checker = ShadowStateChecker(plugin_root=self.plugin_root)
        config = checker._load_config()
        result = checker._get_essences_path(config)

        # チルダが展開されて絶対パスになる
        assert result.is_absolute()
        assert "~" not in str(result)
        assert "Essences" in str(result)


class TestShadowStateCheckerCLI(unittest.TestCase):
    """CLI エントリーポイントのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self) -> None:

        """プラグイン構造を作成"""
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        config_data = {
            "base_dir": ".",
            "paths": {"essences_dir": "data/Essences"},
        }
        with open(
            self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8"
        ) as f:
            json.dump(config_data, f)

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001"],
                        "digest_type": "テスト",
                        "keywords": ["kw1"],
                        "abstract": "要約",
                        "impression": "所感",
                    }
                }
            },
        }
        with open(
            self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(shadow_data, f)

    @pytest.mark.unit
    def test_main_help_exits_zero(self) -> None:

        """--helpで終了コード0"""
        result = subprocess.run(
            [sys.executable, "-m", "interfaces.shadow_state_checker", "--help"],
            capture_output=True,
            cwd=str(Path(__file__).parent.parent.parent),
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Shadow", result.stdout)


if __name__ == "__main__":
    unittest.main()
