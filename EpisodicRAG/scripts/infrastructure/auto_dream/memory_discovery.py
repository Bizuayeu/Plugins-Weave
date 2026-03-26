#!/usr/bin/env python3
"""
Memory Discovery
================

Claude Code auto-memoryディレクトリの発見。
~/.claude/projects/*/memory/ を探索し、MEMORY.mdが存在するディレクトリを返す。

Usage:
    from infrastructure.auto_dream.memory_discovery import discover_memory_dirs
"""

import re
from pathlib import Path
from typing import List, Optional


def get_claude_projects_base() -> Path:
    """
    Claude Codeのprojectsベースディレクトリを返す

    Returns:
        ~/.claude/projects/ のPath

    Example:
        >>> get_claude_projects_base()
        PosixPath('/home/user/.claude/projects')
    """
    return Path.home() / ".claude" / "projects"


def encode_project_path(project_path: str) -> str:
    """
    プロジェクトパスをClaude Codeのディレクトリ名形式にエンコード

    Claude Codeはプロジェクトの絶対パスをディレクトリ名に変換する際、
    パス区切り文字とコロンをハイフンに置換する。

    Args:
        project_path: プロジェクトの絶対パス（例: "C:\\Users\\anyth\\DEV"）

    Returns:
        エンコード済みディレクトリ名（例: "C--Users-anyth-DEV"）

    Example:
        >>> encode_project_path("C:\\\\Users\\\\anyth\\\\DEV")
        'C--Users-anyth-DEV'
        >>> encode_project_path("/home/user/project")
        '-home-user-project'
    """
    # コロン → ハイフン（Windowsドライブレター "C:" → "C-"）
    encoded = project_path.replace(":", "-")
    # バックスラッシュ → ハイフン
    encoded = encoded.replace("\\", "-")
    # フォワードスラッシュ → ハイフン
    encoded = encoded.replace("/", "-")
    return encoded


def discover_memory_dirs(project_path: Optional[str] = None) -> List[Path]:
    """
    auto-memoryディレクトリを発見

    MEMORY.mdが存在するディレクトリのみを返す。

    Args:
        project_path: 指定時はそのプロジェクトのメモリのみ検索。
                      未指定時は全プロジェクトをglob。

    Returns:
        memory/ディレクトリのPathリスト（ソート済み）

    Example:
        >>> discover_memory_dirs()
        [PosixPath('/home/user/.claude/projects/C--Users-anyth-DEV/memory')]
        >>> discover_memory_dirs("C:\\\\Users\\\\anyth\\\\DEV")
        [PosixPath('/home/user/.claude/projects/C--Users-anyth-DEV/memory')]
    """
    base = get_claude_projects_base()

    if not base.exists():
        return []

    if project_path is not None:
        encoded = encode_project_path(project_path)
        memory_dir = base / encoded / "memory"
        index_file = memory_dir / "MEMORY.md"
        if index_file.exists():
            return [memory_dir]
        return []

    # 全プロジェクトをglob
    found: List[Path] = []
    for index_file in sorted(base.glob("*/memory/MEMORY.md")):
        found.append(index_file.parent)

    return found
