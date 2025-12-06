#!/usr/bin/env python3
"""
digest_readiness.py のテスト
============================

DigestReadinessChecker クラスと CLI エントリーポイントのテスト。
TDD: Red → Green → Refactor
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest


class TestDigestReadinessChecker(unittest.TestCase):
    """DigestReadinessChecker クラスのテスト"""

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
        (self.plugin_root / "data" / "Digests" / "1_Weekly" / "Provisional").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests" / "2_Monthly" / "Provisional").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests" / "3_Quarterly" / "Provisional").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

        # config.json
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "provisional_dir": "data/Provisional",
            },
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 4,
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    def _create_shadow_complete(self, level: str = "weekly") -> None:
        """完備状態のShadowGrandDigestを作成（SDG完備）"""
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001_test.txt", "L00002_test.txt", "L00003_test.txt",
                                         "L00004_test.txt", "L00005_test.txt"],
                        "digest_type": "テスト分析",
                        "keywords": ["キーワード1", "キーワード2", "キーワード3"],
                        "abstract": "これは分析済みの要約です。",
                        "impression": "これは分析済みの所感です。",
                    }
                },
                "monthly": {
                    "overall_digest": {
                        "source_files": ["W0001_test.txt", "W0002_test.txt",
                                         "W0003_test.txt", "W0004_test.txt"],
                        "digest_type": "月次テスト",
                        "keywords": ["月次1", "月次2"],
                        "abstract": "月次要約",
                        "impression": "月次所感",
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

    def _create_shadow_with_placeholders(self, level: str = "weekly") -> None:
        """プレースホルダー付きのShadowGrandDigestを作成（SDG未完備）"""
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001_test.txt", "L00002_test.txt"],
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

    def _create_shadow_missing_source_files(self) -> None:
        """source_filesが不足しているShadowGrandDigestを作成"""
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001_test.txt", "L00002_test.txt"],  # 2件のみ
                        "digest_type": "テスト分析",
                        "keywords": ["キーワード1"],
                        "abstract": "要約",
                        "impression": "所感",
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

    def _create_provisional_complete(self, level: str = "monthly") -> None:
        """完備状態のProvisionalDigestを作成

        levelで指定したレベルのProvisionalディレクトリに作成する
        """
        if level == "monthly":
            # monthlyのsource_filesに対応するProvisionalを作成
            provisional_data = {
                "individual_digests": [
                    {
                        "source_file": "W0001_test.txt",
                        "digest_type": "テスト1",
                        "keywords": ["kw1"],
                        "abstract": {"long": "長い要約1", "short": "短い要約1"},
                        "impression": {"long": "長い所感1", "short": "短い所感1"},
                    },
                    {
                        "source_file": "W0002_test.txt",
                        "digest_type": "テスト2",
                        "keywords": ["kw2"],
                        "abstract": {"long": "長い要約2", "short": "短い要約2"},
                        "impression": {"long": "長い所感2", "short": "短い所感2"},
                    },
                    {
                        "source_file": "W0003_test.txt",
                        "digest_type": "テスト3",
                        "keywords": ["kw3"],
                        "abstract": {"long": "長い要約3", "short": "短い要約3"},
                        "impression": {"long": "長い所感3", "short": "短い所感3"},
                    },
                    {
                        "source_file": "W0004_test.txt",
                        "digest_type": "テスト4",
                        "keywords": ["kw4"],
                        "abstract": {"long": "長い要約4", "short": "短い要約4"},
                        "impression": {"long": "長い所感4", "short": "短い所感4"},
                    },
                ]
            }
            provisional_path = self.plugin_root / "data" / "Digests" / "2_Monthly" / "Provisional" / "M0001_Individual.txt"
        else:
            provisional_data = {"individual_digests": []}
            provisional_path = self.plugin_root / "data" / "Digests" / "3_Quarterly" / "Provisional" / "Q001_Individual.txt"

        with open(provisional_path, "w", encoding="utf-8") as f:
            json.dump(provisional_data, f)

    def _create_provisional_missing(self, level: str = "monthly") -> None:
        """一部欠損のProvisionalDigestを作成"""
        if level == "monthly":
            # W0003_test.txtが欠損
            provisional_data = {
                "individual_digests": [
                    {
                        "source_file": "W0001_test.txt",
                        "digest_type": "テスト1",
                        "keywords": ["kw1"],
                        "abstract": {"long": "長い要約1", "short": "短い要約1"},
                        "impression": {"long": "長い所感1", "short": "短い所感1"},
                    },
                    {
                        "source_file": "W0002_test.txt",
                        "digest_type": "テスト2",
                        "keywords": ["kw2"],
                        "abstract": {"long": "長い要約2", "short": "短い要約2"},
                        "impression": {"long": "長い所感2", "short": "短い所感2"},
                    },
                    # W0003_test.txt が欠損
                    {
                        "source_file": "W0004_test.txt",
                        "digest_type": "テスト4",
                        "keywords": ["kw4"],
                        "abstract": {"long": "長い要約4", "short": "短い要約4"},
                        "impression": {"long": "長い所感4", "short": "短い所感4"},
                    },
                ]
            }
            provisional_path = self.plugin_root / "data" / "Digests" / "2_Monthly" / "Provisional" / "M0001_Individual.txt"
            with open(provisional_path, "w", encoding="utf-8") as f:
                json.dump(provisional_data, f)

    # =========================================================================
    # threshold_met テスト
    # =========================================================================

    @pytest.mark.unit
    def test_threshold_met_true(self) -> None:
        """source_count >= threshold の場合 threshold_met=True"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_complete("weekly")
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertEqual(result.status, "ok")
        self.assertTrue(result.threshold_met)
        self.assertEqual(result.source_count, 5)
        self.assertEqual(result.level_threshold, 5)

    @pytest.mark.unit
    def test_threshold_met_false(self) -> None:
        """source_count < threshold の場合 threshold_met=False"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_missing_source_files()
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertEqual(result.status, "ok")
        self.assertFalse(result.threshold_met)
        self.assertEqual(result.source_count, 2)
        self.assertEqual(result.level_threshold, 5)
        self.assertIn("threshold未達", result.blockers[0])

    # =========================================================================
    # sdg_ready テスト
    # =========================================================================

    @pytest.mark.unit
    def test_sdg_ready_true(self) -> None:
        """SDG完備の場合 sdg_ready=True"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_complete("weekly")
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertTrue(result.sdg_ready)
        self.assertEqual(result.missing_sdg_files, [])

    @pytest.mark.unit
    def test_sdg_ready_false_placeholder(self) -> None:
        """PLACEHOLDERがある場合 sdg_ready=False"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_with_placeholders("weekly")
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertFalse(result.sdg_ready)
        # PLACEHOLDERがある場合のblockerメッセージ
        sdg_blocker = [b for b in result.blockers if "SDG" in b]
        self.assertTrue(len(sdg_blocker) > 0)

    # =========================================================================
    # provisional_ready テスト
    # =========================================================================

    @pytest.mark.unit
    def test_provisional_ready_true(self) -> None:
        """Provisional完備の場合 provisional_ready=True"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_complete("monthly")
        self._create_provisional_complete("monthly")
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("monthly")

        self.assertTrue(result.provisional_ready)
        self.assertEqual(result.missing_provisionals, [])

    @pytest.mark.unit
    def test_provisional_ready_false(self) -> None:
        """Provisionalに欠損がある場合 provisional_ready=False"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_complete("monthly")
        self._create_provisional_missing("monthly")
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("monthly")

        self.assertFalse(result.provisional_ready)
        self.assertIn("W0003_test.txt", result.missing_provisionals)
        prov_blocker = [b for b in result.blockers if "Provisional" in b]
        self.assertTrue(len(prov_blocker) > 0)

    # =========================================================================
    # can_finalize テスト
    # =========================================================================

    @pytest.mark.unit
    def test_can_finalize_true(self) -> None:
        """全条件満たす場合 can_finalize=True"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_complete("monthly")
        self._create_provisional_complete("monthly")
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("monthly")

        self.assertTrue(result.can_finalize)
        self.assertEqual(result.blockers, [])
        self.assertIn("確定可能", result.message)

    @pytest.mark.unit
    def test_can_finalize_false(self) -> None:
        """いずれかの条件が未達の場合 can_finalize=False"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_with_placeholders("weekly")
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        self.assertFalse(result.can_finalize)
        self.assertTrue(len(result.blockers) > 0)
        self.assertIn("確定不可", result.message)

    # =========================================================================
    # blockers テスト
    # =========================================================================

    @pytest.mark.unit
    def test_blockers_output(self) -> None:
        """未達条件がblockersに明示される"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_missing_source_files()
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("weekly")

        # threshold未達のblockerが含まれる
        self.assertTrue(any("threshold" in b for b in result.blockers))

    # =========================================================================
    # エラーケース
    # =========================================================================

    @pytest.mark.unit
    def test_invalid_level_returns_error(self) -> None:
        """無効なレベルの場合エラーを返す"""
        sys.path.insert(0, str(self.plugin_root.parent / "scripts"))
        from interfaces.digest_readiness import DigestReadinessChecker

        self._create_shadow_complete("weekly")
        checker = DigestReadinessChecker(plugin_root=self.plugin_root)
        result = checker.check("invalid_level")

        self.assertEqual(result.status, "error")
        self.assertIn("Invalid level", result.error)


class TestDigestReadinessCLI(unittest.TestCase):
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
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
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
            [sys.executable, "-m", "interfaces.digest_readiness", "--help"],
            capture_output=True,
            cwd=str(Path(__file__).parent.parent.parent),
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("readiness", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
