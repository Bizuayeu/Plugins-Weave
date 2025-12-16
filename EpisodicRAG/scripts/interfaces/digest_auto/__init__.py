#!/usr/bin/env python3
"""
Digest Auto Package
===================

健全性診断CLI。Claudeから呼び出され、システム状態を分析し、
まだらボケを検出、生成可能なダイジェスト階層を推奨する。

Usage:
    python -m interfaces.digest_auto --output json
    python -m interfaces.digest_auto --output text

Modules:
    models: データクラス (Issue, LevelStatus, AnalysisResult)
    path_resolver: パス解決ユーティリティ
    file_scanner: ファイルスキャンユーティリティ
    analyzer: DigestAutoAnalyzer クラス
    report: レポートフォーマット
"""

from dataclasses import asdict

from .analyzer import DigestAutoAnalyzer
from .models import AnalysisResult, Issue, LevelStatus
from .report import MAX_DISPLAY_FILES, format_text_report, print_text_report

__all__ = [
    # Classes
    "DigestAutoAnalyzer",
    "Issue",
    "LevelStatus",
    "AnalysisResult",
    # Functions
    "format_text_report",
    "print_text_report",
    "main",
    # Constants
    "MAX_DISPLAY_FILES",
    # Re-exports
    "asdict",
]


def main() -> None:
    """CLIエントリーポイント"""
    import argparse
    import sys

    from interfaces.cli_helpers import output_error, output_json

    parser = argparse.ArgumentParser(
        description="EpisodicRAG Health Diagnostic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )

    args = parser.parse_args()

    try:
        analyzer = DigestAutoAnalyzer()
        result = analyzer.analyze()

        if args.output == "json":
            output_json(asdict(result))
        else:
            print_text_report(result)

    except Exception as e:
        output_error(str(e))


if __name__ == "__main__":
    import io
    import sys

    # Windows UTF-8入出力対応
    if sys.platform == "win32":
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    main()
