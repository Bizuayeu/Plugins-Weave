#!/usr/bin/env python3
"""
digest_auto の未処理Loop検出ロジックのテスト
=============================================

TDD: Phase 1 (RED) - digest_auto が loop.last_processed を参照することを確認

file_detector.py と同様に、weekly の未処理Loop検出には
loop.last_processed を参照すべき。現在のバグ実装は
weekly.last_processed を参照している。
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import pytest


class TestDigestAutoUnprocessedLoopsDetection(unittest.TestCase):
    """未処理Loop検出が loop.last_processed を参照することを確認"""

    def setUp(self) -> None:
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        # 永続化設定ディレクトリを作成
        self.persistent_config = self.plugin_root / ".persistent_config"
        self.persistent_config.mkdir(parents=True)
        # 環境変数を設定
        self._old_env = os.environ.get("EPISODICRAG_CONFIG_DIR")
        os.environ["EPISODICRAG_CONFIG_DIR"] = str(self.persistent_config)
        self._setup_plugin_structure()

    def tearDown(self) -> None:
        """一時ディレクトリを削除"""
        # 環境変数をリセット
        if self._old_env is not None:
            os.environ["EPISODICRAG_CONFIG_DIR"] = self._old_env
        else:
            os.environ.pop("EPISODICRAG_CONFIG_DIR", None)
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

        # config.json（永続化ディレクトリに）
        config_data = {
            "base_dir": str(self.plugin_root),
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
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # ShadowGrandDigest.txt
        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {"overall_digest": None},
                "monthly": {"overall_digest": None},
            },
        }
        with open(
            self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(shadow_data, f)

        # GrandDigest.txt
        grand_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(
            self.plugin_root / "data" / "Essences" / "GrandDigest.txt",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(grand_data, f)

    @pytest.mark.unit
    def test_uses_loop_last_processed_for_unprocessed_detection(self) -> None:
        """未処理Loop検出時は loop.last_processed を参照すべき

        シナリオ:
        - loop.last_processed = 9 (Loopファイルは L00010 まで処理済み)
        - weekly.last_processed = 2 (Weeklyは W0002 まで確定済み)
        - 実際のLoopファイルは L00001-L00010 が存在

        期待結果:
        - 未処理Loop は 0 件（全て処理済み）

        バグ実装の結果:
        - 未処理Loop は 8 件（L00003-L00010 が未処理と誤検出）
        """
        from interfaces.digest_auto import DigestAutoAnalyzer

        # Arrange: 10個のLoopファイルを作成
        for i in range(1, 11):
            (self.plugin_root / "data" / "Loops" / f"L{i:05d}_Test.txt").write_text("content")

        # last_digest_times.json を設定（永続化ディレクトリに）
        # loop.last_processed = 9 → L00001-L00009 までshadowに追加済み
        # weekly.last_processed = 2 → W0002 まで確定済み（関係ないはず）
        times_data = {
            "loop": {"timestamp": "2025-01-01T00:00:00", "last_processed": 9},
            "weekly": {"timestamp": "2025-01-01T00:00:00", "last_processed": 2},
        }
        with open(
            self.persistent_config / "last_digest_times.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(times_data, f)

        # Act
        analyzer = DigestAutoAnalyzer()
        result = analyzer.analyze()

        # Assert
        unprocessed_issues = [i for i in result.issues if i.type == "unprocessed_loops"]
        if unprocessed_issues:
            unprocessed_count = unprocessed_issues[0].count
        else:
            unprocessed_count = 0

        # 期待: L00010 のみ未処理 → 1件
        # バグ: L00003-L00010 が未処理 → 8件
        assert unprocessed_count == 1, (
            f"Expected 1 unprocessed loop (L00010), but got {unprocessed_count}. "
            f"Bug: using weekly.last_processed instead of loop.last_processed"
        )

    @pytest.mark.unit
    def test_all_loops_processed_when_loop_last_processed_equals_max(self) -> None:
        """loop.last_processed が最大Loop番号と同じなら未処理は0件"""
        from interfaces.digest_auto import DigestAutoAnalyzer

        # Arrange: 5個のLoopファイルを作成
        for i in range(1, 6):
            (self.plugin_root / "data" / "Loops" / f"L{i:05d}_Test.txt").write_text("content")

        # loop.last_processed = 5 → 全て処理済み（永続化ディレクトリに）
        times_data = {
            "loop": {"timestamp": "2025-01-01T00:00:00", "last_processed": 5},
            "weekly": {"timestamp": "2025-01-01T00:00:00", "last_processed": 1},
        }
        with open(
            self.persistent_config / "last_digest_times.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(times_data, f)

        # Act
        analyzer = DigestAutoAnalyzer()
        result = analyzer.analyze()

        # Assert: 未処理は0件
        unprocessed_issues = [i for i in result.issues if i.type == "unprocessed_loops"]
        assert len(unprocessed_issues) == 0, (
            f"Expected 0 unprocessed loops, but found issues: {unprocessed_issues}"
        )


if __name__ == "__main__":
    unittest.main()
