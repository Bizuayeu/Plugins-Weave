#!/usr/bin/env python3
"""
DigestAuto CLI 出力形式テスト
=============================

JSON vs Text 出力形式のテスト。
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


class TestDigestAutoCLIOutputFormats(unittest.TestCase):
    """出力形式テスト（JSON vs Text）"""

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
    def test_json_output_is_valid_json(self) -> None:
        """JSON出力がパース可能"""
        with patch(
            "sys.argv",
            ["digest_auto.py", "--output", "json"],
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)
                assert isinstance(result, dict)

    @pytest.mark.unit
    def test_json_output_contains_required_fields(self) -> None:
        """JSON出力に必須フィールドが含まれる"""
        with patch(
            "sys.argv",
            ["digest_auto.py", "--output", "json"],
        ):
            from interfaces.digest_auto import main

            with patch("builtins.print") as mock_print:
                main()
                output = mock_print.call_args[0][0]
                result = json.loads(output)

                assert "status" in result
                assert result["status"] in ["ok", "warning", "error"]

    @pytest.mark.unit
    def test_text_output_contains_header(self) -> None:
        """テキスト出力にヘッダーが含まれる"""
        from interfaces.digest_auto import AnalysisResult, format_text_report

        result = AnalysisResult(status="ok")
        formatted = format_text_report(result)

        assert "EpisodicRAG システム状態" in formatted
        assert "```text" in formatted

    @pytest.mark.unit
    def test_text_output_contains_status_indicators(self) -> None:
        """テキスト出力にステータスインジケータが含まれる"""
        from interfaces.digest_auto import AnalysisResult, Issue, format_text_report

        # 警告ありの結果を作成
        result = AnalysisResult(
            status="warning",
            issues=[Issue(type="unprocessed_loops", count=2, files=["L00001.txt", "L00002.txt"])],
        )
        formatted = format_text_report(result)

        # 警告インジケータが含まれることを確認
        assert "未処理Loop" in formatted

    @pytest.mark.unit
    def test_error_json_contains_status_error(self) -> None:
        """エラー時にJSON出力がstatus=errorを含む"""
        # ShadowGrandDigestを削除してエラーを発生させる
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
    def test_error_json_contains_error_message(self) -> None:
        """エラー時にJSON出力がerrorメッセージを含む"""
        # ShadowGrandDigestを削除してエラーを発生させる
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
                assert "error" in result
                assert result["error"] is not None


class TestFormatTextReportDisplayLimit:
    """MAX_DISPLAY_FILES による表示切り詰めのテスト"""

    @pytest.mark.unit
    def test_displays_all_files_when_under_limit(self) -> None:
        """5件未満の場合、すべてのファイルを表示"""
        from interfaces.digest_auto import AnalysisResult, Issue, format_text_report

        files = ["L00001.txt", "L00002.txt", "L00003.txt"]
        result = AnalysisResult(
            status="warning",
            issues=[Issue(type="unprocessed_loops", count=3, files=files)],
        )
        formatted = format_text_report(result)

        # すべてのファイルが表示される
        for f in files:
            assert f"  - {f}" in formatted
        # 省略表示がない
        assert "... 他" not in formatted

    @pytest.mark.unit
    def test_boundary_exactly_five_files(self) -> None:
        """境界値: ちょうど5件の場合、省略なし"""
        from interfaces.digest_auto import AnalysisResult, Issue, format_text_report

        files = [f"L0000{i}.txt" for i in range(1, 6)]  # 5件
        result = AnalysisResult(
            status="warning",
            issues=[Issue(type="unprocessed_loops", count=5, files=files)],
        )
        formatted = format_text_report(result)

        # すべてのファイルが表示される
        for f in files:
            assert f"  - {f}" in formatted
        # 省略表示がない
        assert "... 他" not in formatted

    @pytest.mark.unit
    def test_boundary_six_files_truncates_one(self) -> None:
        """境界値: 6件の場合、1件省略"""
        from interfaces.digest_auto import AnalysisResult, Issue, format_text_report

        files = [f"L0000{i}.txt" for i in range(1, 7)]  # 6件
        result = AnalysisResult(
            status="warning",
            issues=[Issue(type="unprocessed_loops", count=6, files=files)],
        )
        formatted = format_text_report(result)

        # 最初の5件が表示される
        for f in files[:5]:
            assert f"  - {f}" in formatted
        # 6件目は表示されない
        assert f"  - {files[5]}" not in formatted
        # 省略表示がある
        assert "... 他1個" in formatted

    @pytest.mark.unit
    def test_truncates_many_files(self) -> None:
        """10件の場合、5件+省略表示"""
        from interfaces.digest_auto import AnalysisResult, Issue, format_text_report

        files = [f"L{i:05d}.txt" for i in range(1, 11)]  # 10件
        result = AnalysisResult(
            status="warning",
            issues=[Issue(type="unprocessed_loops", count=10, files=files)],
        )
        formatted = format_text_report(result)

        # 最初の5件が表示される
        for f in files[:5]:
            assert f"  - {f}" in formatted
        # 6件目以降は表示されない
        for f in files[5:]:
            assert f"  - {f}" not in formatted
        # 省略表示: "... 他5個"
        assert "... 他5個" in formatted

    @pytest.mark.unit
    def test_truncation_message_format(self) -> None:
        """省略メッセージのフォーマット確認: "... 他N個" """
        from interfaces.digest_auto import AnalysisResult, Issue, format_text_report

        files = [f"L{i:05d}.txt" for i in range(1, 8)]  # 7件
        result = AnalysisResult(
            status="warning",
            issues=[Issue(type="unprocessed_loops", count=7, files=files)],
        )
        formatted = format_text_report(result)

        # 正確なフォーマットを確認
        assert "  ... 他2個" in formatted


if __name__ == "__main__":
    unittest.main()
