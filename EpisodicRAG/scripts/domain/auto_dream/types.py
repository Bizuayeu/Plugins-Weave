#!/usr/bin/env python3
"""
Auto-Dream 型定義
=================

Claude Code auto-memoryファイルの構造を表現するTypedDict群。
外部依存なし。

Usage:
    from domain.auto_dream.types import MemoryFile, AutoDreamScanResult
"""

from typing import Dict, List, Literal, Optional, TypedDict

# =============================================================================
# 基本型
# =============================================================================

MemoryType = Literal["user", "feedback", "project", "reference"]
"""auto-memoryファイルの4種別"""

VALID_MEMORY_TYPES = {"user", "feedback", "project", "reference"}
"""MemoryTypeの検証用セット"""


# =============================================================================
# メモリファイル関連
# =============================================================================


class MemoryFileFrontmatter(TypedDict):
    """
    auto-memoryファイルのYAML frontmatter構造

    Example:
        ---
        name: 大環主プロファイル
        description: 対話相手・大環主の役割・認知特性
        type: user
        ---
    """

    name: str
    description: str
    type: MemoryType


class MemoryFile(TypedDict):
    """
    パース済みauto-memoryファイル

    frontmatterとbodyを分離して保持。
    """

    filename: str  # e.g. "user_profile.md"
    path: str  # 絶対パス
    frontmatter: MemoryFileFrontmatter
    content: str  # body（frontmatter除く）
    content_length: int  # bodyの文字数


class MemoryIndex(TypedDict):
    """
    MEMORY.md（インデックスファイル）のパース結果

    セクション別にリンクされたファイル名を保持。
    """

    path: str  # 絶対パス
    sections: Dict[str, List[str]]  # {"User": ["user_profile.md"], ...}
    raw_content: str  # 生テキスト


# =============================================================================
# スキャン結果
# =============================================================================


class AutoDreamScanResult(TypedDict):
    """
    auto_dream_scan CLIの出力構造

    status:
        "ok"        — メモリ発見・スキャン成功
        "no_memory" — メモリディレクトリなし
        "error"     — スキャン中にエラー
    """

    status: str  # "ok" | "no_memory" | "error"
    project_path: Optional[str]  # マッチしたプロジェクトのエンコード名
    memory_dir: Optional[str]  # memory/ディレクトリの絶対パス
    memory_index: Optional[MemoryIndex]
    memory_files: List[MemoryFile]
    file_count: int
    error: Optional[str]
