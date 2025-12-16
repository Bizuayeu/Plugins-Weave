#!/usr/bin/env python3
"""
Digest Auto Models
==================

健全性診断で使用するデータクラス群。

Classes:
    Issue: 検出された問題を表現
    LevelStatus: 階層の状態を表現
    AnalysisResult: 分析結果全体を表現
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

__all__ = [
    "Issue",
    "LevelStatus",
    "AnalysisResult",
    "asdict",
]


@dataclass
class Issue:
    """検出された問題

    Attributes:
        type: 問題の種類 ("unprocessed_loops" | "placeholders" | "gaps")
        level: 関連する階層名（オプション）
        count: 問題の件数
        files: 関連ファイルのリスト
        details: 追加詳細情報（オプション）
    """

    type: str  # "unprocessed_loops" | "placeholders" | "gaps"
    level: Optional[str] = None
    count: int = 0
    files: List[str] = field(default_factory=list)
    details: Optional[Dict[str, Any]] = None


@dataclass
class LevelStatus:
    """階層の状態

    Attributes:
        level: 階層名
        current: 現在の件数
        threshold: 生成に必要な閾値
        ready: 生成可能かどうか
        source_type: ソースの種類 ("loops" | level name)
    """

    level: str
    current: int
    threshold: int
    ready: bool
    source_type: str  # "loops" | level name


@dataclass
class AnalysisResult:
    """分析結果

    Attributes:
        status: 全体ステータス ("ok" | "warning" | "error")
        issues: 検出された問題のリスト
        generatable_levels: 生成可能な階層のリスト
        insufficient_levels: 件数不足の階層のリスト
        recommendations: 推奨アクションのリスト
        error: エラーメッセージ（エラー時のみ）
    """

    status: str  # "ok" | "warning" | "error"
    issues: List[Issue] = field(default_factory=list)
    generatable_levels: List[LevelStatus] = field(default_factory=list)
    insufficient_levels: List[LevelStatus] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    error: Optional[str] = None
