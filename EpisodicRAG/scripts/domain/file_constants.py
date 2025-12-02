#!/usr/bin/env python3
"""
EpisodicRAG ファイル名・パス定数
================================

ファイル名、ディレクトリ名、ファイルパターンのSingle Source of Truth。
外部依存を持たない純粋な定数定義。

Usage:
    from domain.file_constants import (
        GRAND_DIGEST_FILENAME,
        SHADOW_GRAND_DIGEST_FILENAME,
        CONFIG_FILENAME,
    )
"""

# =============================================================================
# Grand Digest ファイル名
# =============================================================================

GRAND_DIGEST_FILENAME = "GrandDigest.txt"
"""確定済みGrand Digestのファイル名"""

SHADOW_GRAND_DIGEST_FILENAME = "ShadowGrandDigest.txt"
"""未確定Shadow Grand Digestのファイル名"""


# =============================================================================
# テンプレートファイル名
# =============================================================================

GRAND_DIGEST_TEMPLATE = "GrandDigest.template.txt"
"""Grand Digestのテンプレートファイル名"""

SHADOW_GRAND_DIGEST_TEMPLATE = "ShadowGrandDigest.template.txt"
"""Shadow Grand Digestのテンプレートファイル名"""

DIGEST_TIMES_TEMPLATE = "last_digest_times.template.json"
"""ダイジェスト生成時刻記録のテンプレートファイル名"""

CONFIG_TEMPLATE = "config.template.json"
"""設定ファイルのテンプレート名"""


# =============================================================================
# 設定ファイル名
# =============================================================================

CONFIG_FILENAME = "config.json"
"""プラグイン設定ファイル名"""

DIGEST_TIMES_FILENAME = "last_digest_times.json"
"""ダイジェスト生成時刻記録ファイル名"""


# =============================================================================
# ディレクトリ名
# =============================================================================

PLUGIN_CONFIG_DIR = ".claude-plugin"
"""プラグイン設定ディレクトリ名（ドット始まり）"""

ESSENCES_DIR_NAME = "Essences"
"""Essences（ダイジェスト格納）ディレクトリ名"""

LOOPS_DIR_NAME = "Loops"
"""Loops（会話ログ格納）ディレクトリ名"""

PROVISIONALS_SUBDIR = "Provisionals"
"""仮ダイジェスト格納サブディレクトリ名"""

DATA_DIR_NAME = "data"
"""データルートディレクトリ名"""


# =============================================================================
# ファイルパターン（glob用）
# =============================================================================

LOOP_FILE_PATTERN = "L*.txt"
"""Loopファイルのglobパターン"""

WEEKLY_FILE_PATTERN = "W*.txt"
"""Weeklyダイジェストのglobパターン"""

MONTHLY_FILE_PATTERN = "M*.txt"
"""Monthlyダイジェストのglobパターン"""


# =============================================================================
# ファイル名サフィックス
# =============================================================================

INDIVIDUAL_DIGEST_SUFFIX = "_Individual.txt"
"""個別ダイジェスト（Provisional）のサフィックス"""

OVERALL_DIGEST_SUFFIX = "_Overall.txt"
"""統合ダイジェスト（Provisional）のサフィックス"""
