#!/usr/bin/env python3
"""
Auto Report テスト
==================

interfaces/digest_auto/report.py のユニットテスト。
v5.2.0 で digest_auto パッケージ分割により追加。

Functions tested:
    - format_text_report: テキスト形式でレポートをフォーマット
    - MAX_DISPLAY_FILES: 表示上限定数
"""

import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from interfaces.digest_auto.models import AnalysisResult, Issue, LevelStatus
from interfaces.digest_auto.report import MAX_DISPLAY_FILES, format_text_report


class TestMaxDisplayFiles(unittest.TestCase):
    """MAX_DISPLAY_FILES 定数のテスト"""

    def test_max_display_files_value(self) -> None:
        """MAX_DISPLAY_FILES は 5"""
        self.assertEqual(MAX_DISPLAY_FILES, 5)


class TestFormatTextReport(unittest.TestCase):
    """format_text_report() のテスト"""

    def test_ok_status_basic(self) -> None:
        """status=ok の基本出力"""
        result = AnalysisResult(status="ok")
        output = format_text_report(result)

        self.assertIn("EpisodicRAG システム状態", output)
        self.assertIn("```text", output)
        self.assertNotIn("エラー", output)

    def test_error_status_with_message(self) -> None:
        """status=error でエラーメッセージを表示"""
        result = AnalysisResult(
            status="error",
            error="config.json が見つかりません",
        )
        output = format_text_report(result)

        self.assertIn("エラー", output)
        self.assertIn("config.json が見つかりません", output)

    def test_error_status_with_recommendations(self) -> None:
        """status=error で推奨アクションも表示"""
        result = AnalysisResult(
            status="error",
            error="設定エラー",
            recommendations=["@digest-setup を実行してください"],
        )
        output = format_text_report(result)

        self.assertIn("エラー", output)
        self.assertIn("@digest-setup を実行してください", output)

    def test_unprocessed_loops_display(self) -> None:
        """未処理Loop検出の表示"""
        result = AnalysisResult(
            status="warning",
            issues=[
                Issue(
                    type="unprocessed_loops",
                    count=3,
                    files=["L00001_test.txt", "L00002_test.txt", "L00003_test.txt"],
                )
            ],
        )
        output = format_text_report(result)

        self.assertIn("未処理Loop検出", output)
        self.assertIn("3個", output)
        self.assertIn("L00001_test.txt", output)

    def test_unprocessed_loops_truncation(self) -> None:
        """6個以上のファイルは省略表示"""
        files = [f"L{i:05d}_test.txt" for i in range(1, 8)]  # 7 files
        result = AnalysisResult(
            status="warning",
            issues=[
                Issue(type="unprocessed_loops", count=7, files=files)
            ],
        )
        output = format_text_report(result)

        # 最初の5個は表示
        self.assertIn("L00001_test.txt", output)
        self.assertIn("L00005_test.txt", output)
        # 6個目以降は省略
        self.assertNotIn("L00006_test.txt", output)
        self.assertIn("他2個", output)

    def test_placeholders_issue(self) -> None:
        """プレースホルダー検出の表示"""
        result = AnalysisResult(
            status="warning",
            issues=[
                Issue(type="placeholders", level="weekly", count=2)
            ],
        )
        output = format_text_report(result)

        self.assertIn("プレースホルダー検出", output)
        self.assertIn("weekly", output)
        self.assertIn("2個", output)

    def test_gaps_issue(self) -> None:
        """ギャップ検出の表示"""
        result = AnalysisResult(
            status="warning",
            issues=[
                Issue(
                    type="gaps",
                    level="weekly",
                    details={"range": "W00001-W00010", "missing": [3, 5, 7]},
                )
            ],
        )
        output = format_text_report(result)

        self.assertIn("中間ファイルスキップ", output)
        self.assertIn("weekly", output)
        self.assertIn("W00001-W00010", output)
        self.assertIn("3個", output)

    def test_generatable_levels_display(self) -> None:
        """生成可能階層の表示"""
        result = AnalysisResult(
            status="ok",
            generatable_levels=[
                LevelStatus(
                    level="weekly",
                    current=6,
                    threshold=5,
                    ready=True,
                    source_type="loops",
                )
            ],
        )
        output = format_text_report(result)

        self.assertIn("生成可能なダイジェスト", output)
        self.assertIn("weekly", output)
        self.assertIn("6/5", output)

    def test_insufficient_levels_display(self) -> None:
        """不足階層の表示"""
        result = AnalysisResult(
            status="ok",
            insufficient_levels=[
                LevelStatus(
                    level="monthly",
                    current=2,
                    threshold=5,
                    ready=False,
                    source_type="weekly",
                )
            ],
        )
        output = format_text_report(result)

        self.assertIn("生成に必要なファイル数", output)
        self.assertIn("monthly", output)
        self.assertIn("2/5", output)
        self.assertIn("あと3個必要", output)

    def test_recommendations_display(self) -> None:
        """推奨アクションの表示"""
        result = AnalysisResult(
            status="warning",
            recommendations=[
                "/digest を実行してください",
                "/digest weekly を実行してください",
            ],
        )
        output = format_text_report(result)

        self.assertIn("推奨アクション", output)
        self.assertIn("1.", output)
        self.assertIn("/digest を実行してください", output)
        self.assertIn("2.", output)

    def test_max_display_files_boundary_exactly_5(self) -> None:
        """MAX_DISPLAY_FILES=5 の境界値テスト（ちょうど5個）"""
        files = [f"L{i:05d}_test.txt" for i in range(1, 6)]  # 5 files
        result = AnalysisResult(
            status="warning",
            issues=[
                Issue(type="unprocessed_loops", count=5, files=files)
            ],
        )
        output = format_text_report(result)

        # 全て表示される
        self.assertIn("L00001_test.txt", output)
        self.assertIn("L00005_test.txt", output)
        # 「他X個」は表示されない
        self.assertNotIn("他", output)


if __name__ == "__main__":
    unittest.main()
