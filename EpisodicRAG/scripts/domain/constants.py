#!/usr/bin/env python3
"""
EpisodicRAG ドメイン定数
========================

レベル設定とプレースホルダー設定のSingle Source of Truth。
外部依存を持たない純粋な定数定義。

Usage:
    from domain.constants import LEVEL_CONFIG, LEVEL_NAMES, PLACEHOLDER_LIMITS
"""

from typing import Dict

# TypedDictを使わず、構造をコメントで明示（domain層は外部依存なし）
# LevelConfigData構造:
#   prefix  - ファイル名プレフィックス（例: W0001, M001, MD01）
#   digits  - 番号の桁数（例: W0001は4桁）
#   dir     - digests_path 以下のサブディレクトリ名
#   source  - この階層を生成する際の入力元（"loops" または下位階層名）
#   next    - 確定時にカスケードする上位階層（None = 最上位）


# =============================================================================
# ソースタイプ定数
# =============================================================================

SOURCE_TYPE_LOOPS = "loops"  # Loopファイルをソースとするレベル（weekly）


# =============================================================================
# 共通定数: レベル設定（Single Source of Truth）
# =============================================================================

LEVEL_CONFIG: Dict[str, Dict[str, object]] = {
    "weekly": {
        "prefix": "W",
        "digits": 4,
        "dir": "1_Weekly",
        "source": SOURCE_TYPE_LOOPS,
        "next": "monthly",
    },
    "monthly": {
        "prefix": "M",
        "digits": 3,
        "dir": "2_Monthly",
        "source": "weekly",
        "next": "quarterly",
    },
    "quarterly": {
        "prefix": "Q",
        "digits": 3,
        "dir": "3_Quarterly",
        "source": "monthly",
        "next": "annual",
    },
    "annual": {
        "prefix": "A",
        "digits": 2,
        "dir": "4_Annual",
        "source": "quarterly",
        "next": "triennial",
    },
    "triennial": {
        "prefix": "T",
        "digits": 2,
        "dir": "5_Triennial",
        "source": "annual",
        "next": "decadal",
    },
    "decadal": {
        "prefix": "D",
        "digits": 2,
        "dir": "6_Decadal",
        "source": "triennial",
        "next": "multi_decadal",
    },
    "multi_decadal": {
        "prefix": "MD",
        "digits": 2,
        "dir": "7_Multi-decadal",
        "source": "decadal",
        "next": "centurial",
    },
    "centurial": {
        "prefix": "C",
        "digits": 2,
        "dir": "8_Centurial",
        "source": "multi_decadal",
        "next": None,
    },
}

LEVEL_NAMES = list(LEVEL_CONFIG.keys())


# =============================================================================
# プレースホルダー設定
# =============================================================================

# プレースホルダー文字数制限（Claudeへのガイドライン）
PLACEHOLDER_LIMITS: Dict[str, int] = {
    "abstract_chars": 2400,  # abstract（全体統合分析）の文字数
    "impression_chars": 800,  # impression（所感・展望）の文字数
    "keyword_count": 5,  # キーワードの個数
}

# プレースホルダーマーカー（Single Source of Truth）
PLACEHOLDER_MARKER = "<!-- PLACEHOLDER"
PLACEHOLDER_END = " -->"
PLACEHOLDER_SIMPLE = f"{PLACEHOLDER_MARKER}{PLACEHOLDER_END}"  # "<!-- PLACEHOLDER -->"


# =============================================================================
# デフォルトしきい値
# =============================================================================

DEFAULT_THRESHOLDS: Dict[str, int] = {
    "weekly": 5,
    "monthly": 5,
    "quarterly": 3,
    "annual": 4,
    "triennial": 3,
    "decadal": 3,
    "multi_decadal": 3,
    "centurial": 4,
}


# =============================================================================
# ログ出力用定数
# =============================================================================

LOG_SEPARATOR = "=" * 60  # ログ出力用のセパレータ


# =============================================================================
# プレースホルダーファクトリー関数（SSoT）
# =============================================================================


def create_placeholder_text(content_type: str, char_limit: int) -> str:
    """
    プレースホルダーテキストを生成（Single Source of Truth）

    Args:
        content_type: コンテンツタイプ（例: "全体統合分析", "所感・展望"）
        char_limit: 文字数制限

    Returns:
        プレースホルダー文字列

    Example:
        create_placeholder_text("全体統合分析", 2400)
        # -> "<!-- PLACEHOLDER: 全体統合分析 (2400文字程度) -->"
    """
    return f"{PLACEHOLDER_MARKER}: {content_type} ({char_limit}文字程度){PLACEHOLDER_END}"


def create_placeholder_keywords(count: int) -> list:
    """
    キーワードプレースホルダーリストを生成（Single Source of Truth）

    Args:
        count: キーワード数

    Returns:
        プレースホルダーキーワードのリスト

    Example:
        create_placeholder_keywords(5)
        # -> ["<!-- PLACEHOLDER: keyword1 -->", ..., "<!-- PLACEHOLDER: keyword5 -->"]
    """
    return [f"{PLACEHOLDER_MARKER}: keyword{i}{PLACEHOLDER_END}" for i in range(1, count + 1)]
