#!/usr/bin/env python3
"""
DigestAutoAnalyzer クラスのテスト
=================================

DigestAutoAnalyzer クラスの基本機能とヘルパーメソッドのテスト。
test_digest_auto.py から分割。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pytest


class TestDigestAutoAnalyzer(unittest.TestCase):
    """DigestAutoAnalyzer クラスのテスト"""

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

        # Digestサブディレクトリ
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
            (self.plugin_root / "data" / "Digests" / subdir).mkdir()
            (self.plugin_root / "data" / "Digests" / subdir / "Provisional").mkdir()

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
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # ShadowGrandDigest.txt
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {"overall_digest": None},
                "monthly": {"overall_digest": None},
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        # GrandDigest.txt
        grand_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(self.plugin_root / "data" / "Essences" / "GrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(grand_data, f)

        # last_digest_times.json
        times_data = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8") as f:
            json.dump(times_data, f)

    @pytest.mark.unit
    def test_analyze_returns_ok_when_no_issues(self) -> None:

        """問題がない場合に ok を返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        assert result.status == "ok"
        assert len(result.issues) == 0

    @pytest.mark.unit
    def test_analyze_detects_unprocessed_loops(self) -> None:

        """未処理Loopを検出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # Loopファイルを作成
        (self.plugin_root / "data" / "Loops" / "L00001_Test.txt").write_text("content")
        (self.plugin_root / "data" / "Loops" / "L00002_Test.txt").write_text("content")

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        # 未処理Loopの問題が検出される
        unprocessed_issues = [i for i in result.issues if i.type == "unprocessed_loops"]
        assert len(unprocessed_issues) == 1
        assert unprocessed_issues[0].count == 2

    @pytest.mark.unit
    def test_analyze_detects_placeholders(self) -> None:

        """プレースホルダーを検出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # プレースホルダー付きのShadowを作成
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001", "L00002"],
                        "abstract": "<!-- PLACEHOLDER: abstract -->",
                    }
                },
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        placeholder_issues = [i for i in result.issues if i.type == "placeholders"]
        assert len(placeholder_issues) == 1
        assert placeholder_issues[0].level == "weekly"

    @pytest.mark.unit
    def test_analyze_detects_gaps(self) -> None:

        """中間ファイルのギャップを検出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # ギャップのあるsource_filesを持つShadowを作成
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {
                    "overall_digest": {
                        "source_files": ["L00001", "L00003", "L00005"],  # L00002, L00004 が欠番
                        "abstract": "completed abstract",
                    }
                },
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        gap_issues = [i for i in result.issues if i.type == "gaps"]
        assert len(gap_issues) == 1
        assert gap_issues[0].count == 2  # 2つの欠番

    @pytest.mark.unit
    def test_analyze_determines_generatable_levels(self) -> None:

        """生成可能な階層を判定する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # 5つのLoopファイルを作成（weekly thresholdを満たす）
        for i in range(1, 6):
            (self.plugin_root / "data" / "Loops" / f"L{i:05d}_Test.txt").write_text("content")

        # last_processedを更新して未処理扱いにしない
        times_data = {"weekly": {"timestamp": "2025-01-01T00:00:00", "last_processed": 5}}
        with open(self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8") as f:
            json.dump(times_data, f)

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        # weeklyが生成可能
        weekly_levels = [l for l in result.generatable_levels if l.level == "weekly"]
        assert len(weekly_levels) == 1
        assert weekly_levels[0].ready is True

    @pytest.mark.unit
    def test_analyze_includes_recommendations(self) -> None:

        """推奨アクションが含まれる"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # 未処理Loopを作成
        (self.plugin_root / "data" / "Loops" / "L00001_Test.txt").write_text("content")

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        assert len(result.recommendations) > 0

    @pytest.mark.unit
    def test_analyze_returns_error_when_config_missing(self) -> None:

        """設定ファイルがない場合にエラーを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # config.jsonを削除
        (self.plugin_root / ".claude-plugin" / "config.json").unlink()

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        assert result.status == "error"
        assert result.error is not None

    @pytest.mark.unit
    def test_analyze_returns_error_when_shadow_missing(self) -> None:

        """ShadowGrandDigestがない場合にエラーを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # ShadowGrandDigest.txtを削除
        (self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt").unlink()

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer.analyze()

        assert result.status == "error"


class TestDigestAutoAnalyzerHelpers(unittest.TestCase):
    """DigestAutoAnalyzer ヘルパーメソッドのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_extract_file_number(self) -> None:

        """ファイル名から番号を抽出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)

        assert analyzer._extract_file_number("L00001_Test.txt") == 1
        assert analyzer._extract_file_number("W0005_Weekly.txt") == 5
        assert analyzer._extract_file_number("M003_Monthly.txt") == 3
        assert analyzer._extract_file_number("invalid") is None

    @pytest.mark.unit
    def test_find_gaps(self) -> None:

        """連番のギャップを検出する"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)

        assert analyzer._find_gaps([1, 2, 3]) == []
        assert analyzer._find_gaps([1, 3, 5]) == [2, 4]
        assert analyzer._find_gaps([1]) == []
        assert analyzer._find_gaps([]) == []

    @pytest.mark.unit
    def test_load_json_file_returns_none_for_invalid_json(self) -> None:

        """無効なJSONファイルに対してNoneを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # 無効なJSONファイルを作成
        invalid_json_file = self.plugin_root / "invalid.json"
        invalid_json_file.write_text("{ invalid json content")

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer._load_json_file(invalid_json_file)

        assert result is None

    @pytest.mark.unit
    def test_load_json_file_returns_none_for_missing_file(self) -> None:

        """存在しないファイルに対してNoneを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer._load_json_file(self.plugin_root / "nonexistent.json")

        assert result is None

    @pytest.mark.unit
    def test_load_json_file_returns_data_for_valid_json(self) -> None:

        """有効なJSONファイルに対してデータを返す"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # 有効なJSONファイルを作成
        valid_json_file = self.plugin_root / "valid.json"
        valid_json_file.write_text('{"key": "value"}')

        analyzer = DigestAutoAnalyzer(plugin_root=self.plugin_root)
        result = analyzer._load_json_file(valid_json_file)

        assert result is not None
        assert result["key"] == "value"


if __name__ == "__main__":
    unittest.main()
