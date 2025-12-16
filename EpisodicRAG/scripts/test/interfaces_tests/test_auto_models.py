#!/usr/bin/env python3
"""
Auto Models テスト
==================

interfaces/digest_auto/models.py のユニットテスト。
v5.2.0 で digest_auto パッケージ分割により追加。

Classes tested:
    - Issue: 問題データクラス
    - LevelStatus: 階層状態データクラス
    - AnalysisResult: 分析結果データクラス
"""

import json
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from interfaces.digest_auto.models import AnalysisResult, Issue, LevelStatus


class TestIssue(unittest.TestCase):
    """Issue データクラスのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値の確認"""
        issue = Issue(type="unprocessed_loops")

        self.assertEqual(issue.type, "unprocessed_loops")
        self.assertIsNone(issue.level)
        self.assertEqual(issue.count, 0)
        self.assertEqual(issue.files, [])
        self.assertIsNone(issue.details)

    def test_all_fields(self) -> None:
        """全フィールドを指定"""
        issue = Issue(
            type="gaps",
            level="weekly",
            count=3,
            files=["file1.txt", "file2.txt"],
            details={"range": "W00001-W00010"},
        )

        self.assertEqual(issue.type, "gaps")
        self.assertEqual(issue.level, "weekly")
        self.assertEqual(issue.count, 3)
        self.assertEqual(issue.files, ["file1.txt", "file2.txt"])
        self.assertEqual(issue.details, {"range": "W00001-W00010"})

    def test_asdict_serialization(self) -> None:
        """asdict()でdict変換"""
        issue = Issue(type="placeholders", level="monthly", count=2)
        d = asdict(issue)

        self.assertIsInstance(d, dict)
        self.assertEqual(d["type"], "placeholders")
        self.assertEqual(d["level"], "monthly")
        self.assertEqual(d["count"], 2)

    def test_json_serialization(self) -> None:
        """JSON出力可能"""
        issue = Issue(
            type="unprocessed_loops",
            count=5,
            files=["a.txt", "b.txt"],
        )
        json_str = json.dumps(asdict(issue), ensure_ascii=False)

        self.assertIn("unprocessed_loops", json_str)
        self.assertIn("a.txt", json_str)


class TestLevelStatus(unittest.TestCase):
    """LevelStatus データクラスのテスト"""

    def test_all_fields_required(self) -> None:
        """全フィールドが必須（位置引数）"""
        status = LevelStatus(
            level="weekly",
            current=6,
            threshold=5,
            ready=True,
            source_type="loops",
        )

        self.assertEqual(status.level, "weekly")
        self.assertEqual(status.current, 6)
        self.assertEqual(status.threshold, 5)
        self.assertTrue(status.ready)
        self.assertEqual(status.source_type, "loops")

    def test_asdict_serialization(self) -> None:
        """asdict()でdict変換"""
        status = LevelStatus(
            level="monthly",
            current=3,
            threshold=5,
            ready=False,
            source_type="weekly",
        )
        d = asdict(status)

        self.assertIsInstance(d, dict)
        self.assertEqual(d["level"], "monthly")
        self.assertEqual(d["current"], 3)
        self.assertEqual(d["threshold"], 5)
        self.assertFalse(d["ready"])

    def test_json_serialization(self) -> None:
        """JSON出力可能"""
        status = LevelStatus(
            level="quarterly",
            current=2,
            threshold=3,
            ready=False,
            source_type="monthly",
        )
        json_str = json.dumps(asdict(status))

        self.assertIn("quarterly", json_str)
        self.assertIn('"current": 2', json_str)


class TestAnalysisResult(unittest.TestCase):
    """AnalysisResult データクラスのテスト"""

    def test_default_values(self) -> None:
        """リストフィールドの初期値は空リスト"""
        result = AnalysisResult(status="ok")

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.issues, [])
        self.assertEqual(result.generatable_levels, [])
        self.assertEqual(result.insufficient_levels, [])
        self.assertEqual(result.recommendations, [])
        self.assertIsNone(result.error)

    def test_error_status_with_message(self) -> None:
        """エラーステータスとメッセージ"""
        result = AnalysisResult(
            status="error",
            error="config.json が見つかりません",
        )

        self.assertEqual(result.status, "error")
        self.assertEqual(result.error, "config.json が見つかりません")

    def test_nested_asdict(self) -> None:
        """ネストしたdataclassもdict化"""
        result = AnalysisResult(
            status="warning",
            issues=[
                Issue(type="unprocessed_loops", count=3),
            ],
            generatable_levels=[
                LevelStatus(
                    level="weekly",
                    current=6,
                    threshold=5,
                    ready=True,
                    source_type="loops",
                ),
            ],
        )
        d = asdict(result)

        self.assertIsInstance(d, dict)
        self.assertIsInstance(d["issues"], list)
        self.assertIsInstance(d["issues"][0], dict)
        self.assertEqual(d["issues"][0]["type"], "unprocessed_loops")
        self.assertIsInstance(d["generatable_levels"][0], dict)
        self.assertEqual(d["generatable_levels"][0]["level"], "weekly")

    def test_json_serializable(self) -> None:
        """json.dumps()で出力可能"""
        result = AnalysisResult(
            status="warning",
            issues=[
                Issue(type="placeholders", level="weekly", count=1),
            ],
            recommendations=["Run /digest"],
        )
        json_str = json.dumps(asdict(result), ensure_ascii=False)

        self.assertIn("warning", json_str)
        self.assertIn("placeholders", json_str)
        self.assertIn("Run /digest", json_str)

    def test_complex_result(self) -> None:
        """複雑な分析結果の構築"""
        result = AnalysisResult(
            status="warning",
            issues=[
                Issue(type="unprocessed_loops", count=5, files=["a.txt", "b.txt"]),
                Issue(type="gaps", level="weekly", details={"missing": [3, 5]}),
            ],
            generatable_levels=[
                LevelStatus("weekly", 6, 5, True, "loops"),
            ],
            insufficient_levels=[
                LevelStatus("monthly", 2, 5, False, "weekly"),
            ],
            recommendations=[
                "/digest を実行してください",
                "/digest weekly で確定してください",
            ],
        )

        self.assertEqual(len(result.issues), 2)
        self.assertEqual(len(result.generatable_levels), 1)
        self.assertEqual(len(result.insufficient_levels), 1)
        self.assertEqual(len(result.recommendations), 2)

        # JSON変換も問題なし
        json_str = json.dumps(asdict(result), ensure_ascii=False)
        self.assertIn("unprocessed_loops", json_str)


if __name__ == "__main__":
    unittest.main()
