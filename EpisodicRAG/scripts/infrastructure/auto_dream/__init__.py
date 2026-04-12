#!/usr/bin/env python3
"""
Auto-Dream インフラストラクチャ層
================================

auto-memoryディレクトリの発見とファイル読み込み。

Usage:
    from infrastructure.auto_dream import discover_memory_dirs, read_memory_file
"""

from infrastructure.auto_dream.memory_discovery import (
    discover_memory_dirs,
    encode_project_path,
    get_claude_projects_base,
    resolve_project_from_path,
)
from infrastructure.auto_dream.memory_reader import (
    parse_frontmatter,
    read_memory_file,
    read_memory_index,
)

__all__ = [
    "discover_memory_dirs",
    "encode_project_path",
    "get_claude_projects_base",
    "parse_frontmatter",
    "read_memory_file",
    "read_memory_index",
    "resolve_project_from_path",
]
