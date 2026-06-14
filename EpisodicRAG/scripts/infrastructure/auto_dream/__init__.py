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
from infrastructure.auto_dream.index_writer import (
    apply_index,
    rebuild_index_text,
)
from infrastructure.auto_dream.memory_reader import (
    parse_frontmatter,
    read_memory_file,
    read_memory_index,
)
from infrastructure.auto_dream.snapshot_writer import (
    create_snapshot,
    default_snapshot_root,
)

__all__ = [
    # discovery / reader（足す dream＝auto_dream_scan）
    "discover_memory_dirs",
    "encode_project_path",
    "get_claude_projects_base",
    "parse_frontmatter",
    "read_memory_file",
    "read_memory_index",
    "resolve_project_from_path",
    # snapshot / index writer（引く dream＝dream-defrag）
    "apply_index",
    "create_snapshot",
    "default_snapshot_root",
    "rebuild_index_text",
]
