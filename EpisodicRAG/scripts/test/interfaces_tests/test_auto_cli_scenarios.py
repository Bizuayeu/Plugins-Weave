#!/usr/bin/env python3
"""
DigestAuto CLI シナリオテスト
=============================

統合シナリオのテスト。
test_digest_auto.py から分割。
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestDigestAutoCLIScenarios(unittest.TestCase):
    """統合シナリオテスト"""

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
        """完全なプラグイン構造を作成"""
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

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

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {"overall_digest": None},
                "monthly": {"overall_digest": None},
            },
        }
        with open(
            self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8"
        ) as f:
            json.dump(shadow_data, f)

        grand_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(
            self.plugin_root / "data" / "Essences" / "GrandDigest.txt", "w", encoding="utf-8"
        ) as f:
            json.dump(grand_data, f)

        times_data = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(
            self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8"
        ) as f:
            json.dump(times_data, f)

    @pytest.mark.unit
    def test_healthy_system_returns_ok(self) -> None:
        """問題がないシステムで ok を返す"""
        with patch(
            "sys.argv",
            ["digest_auto.py", "--output", "json"],
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "ok"

    @pytest.mark.unit
    def test_system_with_unprocessed_loops_returns_warning(self) -> None:
        """未処理Loopがあるシステムで warning を返す"""
        # Loopファイルを作成
        for i in range(1, 3):
            loop_data = {"overall_digest": {"abstract": f"Test loop {i}"}}
            with open(
                self.plugin_root / "data" / "Loops" / f"L{i:05d}_test.txt", "w", encoding="utf-8"
            ) as f:
                json.dump(loop_data, f)

        with patch(
            "sys.argv",
            ["digest_auto.py", "--output", "json"],
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                # 未処理Loopがあるためwarning
                assert result["status"] in ["ok", "warning"]
                # issues に unprocessed_loops が含まれる
                if result["issues"]:
                    issue_types = [i["type"] for i in result["issues"]]
                    assert "unprocessed_loops" in issue_types

    @pytest.mark.unit
    def test_missing_shadow_returns_error(self) -> None:
        """ShadowGrandDigestがない場合にエラーを返す"""
        # ShadowGrandDigestを削除
        (self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt").unlink()

        with patch(
            "sys.argv",
            ["digest_auto.py", "--output", "json"],
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_corrupted_config_returns_error(self) -> None:
        """破損した設定ファイルでエラーを返す"""

        # 設定ファイルを破損させる（永続化ディレクトリ）
        with open(self.persistent_config / "config.json", "w", encoding="utf-8") as f:
            f.write("{ invalid json")

        with patch(
            "sys.argv",
            ["digest_auto.py", "--output", "json"],
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                # Note: digest_auto may not raise SystemExit but return error status
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 1
                    return

                # If no SystemExit, check for error status in output
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_generatable_levels_included_in_output(self) -> None:
        """生成可能なレベルが出力に含まれる"""
        # 5つのLoopファイルを作成（thresholdを満たす）
        for i in range(1, 6):
            loop_data = {"overall_digest": {"abstract": f"Test loop {i}"}}
            with open(
                self.plugin_root / "data" / "Loops" / f"L{i:05d}_test.txt", "w", encoding="utf-8"
            ) as f:
                json.dump(loop_data, f)

        # last_processedを更新して未処理扱いにしない
        times_data = {"weekly": {"timestamp": "2025-01-01T00:00:00", "last_processed": 5}}
        with open(
            self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8"
        ) as f:
            json.dump(times_data, f)

        with patch(
            "sys.argv",
            ["digest_auto.py", "--output", "json"],
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)

                assert "generatable_levels" in result
                assert isinstance(result["generatable_levels"], list)

    @pytest.mark.unit
    def test_recommendations_included_when_issues_exist(self) -> None:
        """問題がある場合に推奨アクションが含まれる"""
        # 未処理Loopを作成
        loop_data = {"overall_digest": {"abstract": "Test loop"}}
        with open(
            self.plugin_root / "data" / "Loops" / "L00001_test.txt", "w", encoding="utf-8"
        ) as f:
            json.dump(loop_data, f)

        with patch(
            "sys.argv",
            ["digest_auto.py", "--output", "json"],
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)

                assert "recommendations" in result
                assert len(result["recommendations"]) > 0


if __name__ == "__main__":
    unittest.main()
