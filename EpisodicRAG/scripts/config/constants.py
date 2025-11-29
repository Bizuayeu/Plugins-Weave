#!/usr/bin/env python3
"""
Config層専用の定数
==================

Config層をDomain層から独立させるための定数定義。
レベル設定のSingle Source of Truth（Config層版）。

Note:
    Domain層にも同様の定数が存在するが、Config層の独立性を
    保つために重複を許容している。これは意図的な設計決定。

Usage:
    from config.constants import LEVEL_CONFIG, LEVEL_NAMES, SOURCE_TYPE_LOOPS
"""

from typing import Dict, List

# =============================================================================
# ソースタイプ定数
# =============================================================================

SOURCE_TYPE_LOOPS = "loops"  # Loopファイルをソースとするレベル（weekly）


# =============================================================================
# 共通定数: レベル設定（Single Source of Truth for Config Layer）
# =============================================================================

# LevelConfigData構造:
#   prefix    - ファイル名プレフィックス（例: W0001, M001, MD01）
#   digits    - 番号の桁数（例: W0001は4桁）
#   dir       - digests_path 以下のサブディレクトリ名
#   source    - この階層を生成する際の入力元（"loops" または下位階層名）
#   next      - 確定時にカスケードする上位階層（None = 最上位）
#   threshold - このレベルでダイジェスト生成に必要なソースファイル数

LEVEL_CONFIG: Dict[str, Dict[str, object]] = {
    "weekly": {
        "prefix": "W",
        "digits": 4,
        "dir": "1_Weekly",
        "source": SOURCE_TYPE_LOOPS,
        "next": "monthly",
        "threshold": 5,
    },
    "monthly": {
        "prefix": "M",
        "digits": 4,
        "dir": "2_Monthly",
        "source": "weekly",
        "next": "quarterly",
        "threshold": 5,
    },
    "quarterly": {
        "prefix": "Q",
        "digits": 3,
        "dir": "3_Quarterly",
        "source": "monthly",
        "next": "annual",
        "threshold": 3,
    },
    "annual": {
        "prefix": "A",
        "digits": 3,
        "dir": "4_Annual",
        "source": "quarterly",
        "next": "triennial",
        "threshold": 4,
    },
    "triennial": {
        "prefix": "T",
        "digits": 2,
        "dir": "5_Triennial",
        "source": "annual",
        "next": "decadal",
        "threshold": 3,
    },
    "decadal": {
        "prefix": "D",
        "digits": 2,
        "dir": "6_Decadal",
        "source": "triennial",
        "next": "multi_decadal",
        "threshold": 3,
    },
    "multi_decadal": {
        "prefix": "MD",
        "digits": 2,
        "dir": "7_Multi-decadal",
        "source": "decadal",
        "next": "centurial",
        "threshold": 3,
    },
    "centurial": {
        "prefix": "C",
        "digits": 2,
        "dir": "8_Centurial",
        "source": "multi_decadal",
        "next": None,
        "threshold": 4,
    },
}

LEVEL_NAMES: List[str] = list(LEVEL_CONFIG.keys())
