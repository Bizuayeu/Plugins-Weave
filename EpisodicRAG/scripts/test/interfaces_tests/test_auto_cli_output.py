#!/usr/bin/env python3
"""
DigestAuto CLI 出力形式テスト
=============================

JSON vs Text 出力形式のテスト。
test_digest_auto.py から分割。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest


class TestDigestAutoCLIOutputFormats(unittest.TestCase):
    """出力形式テスト（JSON vs Text）"""

    def setUp(self):
        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        self._setup_plugin_structure()

    def tearDown(self):
        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _setup_plugin_structure(self):
        """プラグイン構造を作成"""
        (self.plugin_root / "data" / "Loops").mkdir(parents=True)
        (self.plugin_root / "data" / "Digests").mkdir(parents=True)
        (self.plugin_root / "data" / "Essences").mkdir(parents=True)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

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
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        shadow_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "latest_digests": {
                "weekly": {"overall_digest": None},
                "monthly": {"overall_digest": None},
            },
        }
        with open(self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

        grand_data = {
            "metadata": {"last_updated": "2025-01-01T00:00:00", "version": "1.0"},
            "major_digests": {},
        }
        with open(self.plugin_root / "data" / "Essences" / "GrandDigest.txt", "w", encoding="utf-8") as f:
            json.dump(grand_data, f)

        times_data = {"weekly": {"timestamp": "", "last_processed": None}}
        with open(self.plugin_root / ".claude-plugin" / "last_digest_times.json", "w", encoding="utf-8") as f:
            json.dump(times_data, f)

    @pytest.mark.unit
    def test_json_output_is_valid_json(self):
        """JSON出力がパース可能"""
        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_json_output_contains_required_fields(self):
        """JSON出力に必須フィールドが含まれる"""
        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)

                assert "status" in result
                assert result["status"] in ["ok", "warning", "error"]

    @pytest.mark.unit
    def test_text_output_contains_header(self):
        """テキスト出力にヘッダーが含まれる"""
        from interfaces.digest_auto import AnalysisResult, format_text_report

        result = AnalysisResult(status="ok")
        formatted = format_text_report(result)

        assert "📊 EpisodicRAG システム状態" in formatted
        assert "```text" in formatted

    @pytest.mark.unit
    def test_text_output_contains_status_indicators(self):
        """テキスト出力にステータスインジケータが含まれる"""
        from interfaces.digest_auto import AnalysisResult, Issue, format_text_report

        # 警告ありの結果を作成
        result = AnalysisResult(
            status="warning",
            issues=[Issue(type="unprocessed_loops", count=2, files=["L00001.txt", "L00002.txt"])]
        )
        formatted = format_text_report(result)

        # 警告インジケータが含まれることを確認
        assert "⚠️" in formatted
        assert "未処理Loop" in formatted

    @pytest.mark.unit
    def test_error_json_contains_status_error(self):
        """エラー時にJSON出力がstatus=errorを含む"""
        # ShadowGrandDigestを削除してエラーを発生させる
        (self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt").unlink()

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert result["status"] == "error"

    @pytest.mark.unit
    def test_error_json_contains_error_message(self):
        """エラー時にJSON出力がerrorメッセージを含む"""
        # ShadowGrandDigestを削除してエラーを発生させる
        (self.plugin_root / "data" / "Essences" / "ShadowGrandDigest.txt").unlink()

        with patch("sys.argv", [
            "digest_auto.py",
            "--output", "json",
            "--plugin-root", str(self.plugin_root)
        ]):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert "error" in result
                assert result["error"] is not None


if __name__ == "__main__":
    unittest.main()
