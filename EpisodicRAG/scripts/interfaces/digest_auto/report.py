#!/usr/bin/env python3
"""
Digest Auto Report
==================

分析結果のレポートフォーマット。

Functions:
    format_text_report: テキスト形式でレポートをフォーマット
    print_text_report: テキストレポートを出力
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import AnalysisResult

__all__ = [
    "format_text_report",
    "print_text_report",
    "MAX_DISPLAY_FILES",
]

# 表示制限の定数
MAX_DISPLAY_FILES = 5  # テキストレポートに表示する最大ファイル数


def format_text_report(result: "AnalysisResult") -> str:
    """テキスト形式でレポートをフォーマット（テスト可能）

    Args:
        result: 分析結果

    Returns:
        フォーマットされたテキストレポート
    """
    output = []
    output.append("```text")
    output.append("━" * 40)
    output.append("📊 EpisodicRAG システム状態")
    output.append("━" * 40)
    output.append("")

    # エラーの場合
    if result.status == "error":
        output.append(f"❌ エラー: {result.error}")
        if result.recommendations:
            output.append("")
            for rec in result.recommendations:
                output.append(f"  → {rec}")
        output.append("")
        output.append("━" * 40)
        output.append("```")
        return "\n".join(output)

    # 問題の表示
    if result.issues:
        for issue in result.issues:
            if issue.type == "unprocessed_loops":
                output.append(f"⚠️ 未処理Loop検出: {issue.count}個")
                for f in issue.files[:MAX_DISPLAY_FILES]:
                    output.append(f"  - {f}")
                if len(issue.files) > MAX_DISPLAY_FILES:
                    output.append(f"  ... 他{len(issue.files) - MAX_DISPLAY_FILES}個")
                output.append("")

            elif issue.type == "placeholders":
                output.append(f"⚠️ プレースホルダー検出 ({issue.level}): {issue.count}個")
                output.append("")

            elif issue.type == "gaps":
                output.append(f"⚠️ 中間ファイルスキップ ({issue.level})")
                if issue.details:
                    output.append(f"  範囲: {issue.details.get('range', '')}")
                    missing = issue.details.get("missing", [])
                    output.append(f"  欠番: {len(missing)}個")
                output.append("")

    # 生成可能な階層
    if result.generatable_levels:
        output.append("✅ 生成可能なダイジェスト")
        for level in result.generatable_levels:
            output.append(f"  ✅ {level.level} ({level.current}/{level.threshold})")
        output.append("")

    # 不足している階層
    if result.insufficient_levels:
        output.append("⏳ 生成に必要なファイル数")
        for level in result.insufficient_levels:
            need = level.threshold - level.current
            output.append(
                f"  ❌ {level.level} ({level.current}/{level.threshold}) - あと{need}個必要"
            )
        output.append("")

    # 推奨アクション
    if result.recommendations:
        output.append("━" * 40)
        output.append("📈 推奨アクション")
        output.append("━" * 40)
        for i, rec in enumerate(result.recommendations, 1):
            output.append(f"  {i}. {rec}")
        output.append("")

    output.append("━" * 40)
    output.append("```")
    return "\n".join(output)


def print_text_report(result: "AnalysisResult") -> None:
    """テキスト形式でレポートを出力（VSCode対応）

    Args:
        result: 分析結果
    """
    print(format_text_report(result))
