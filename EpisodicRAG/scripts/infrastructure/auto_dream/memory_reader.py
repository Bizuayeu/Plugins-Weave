#!/usr/bin/env python3
"""
Memory Reader
=============

auto-memoryファイルの読み込みとfrontmatter解析。
PyYAML不使用（依存ゼロ維持）。--- 区切り + : 分割で十分。

Usage:
    from infrastructure.auto_dream.memory_reader import read_memory_file
"""

import re
from pathlib import Path

from domain.auto_dream.types import (
    VALID_MEMORY_TYPES,
    MemoryFile,
    MemoryFileFrontmatter,
    MemoryIndex,
)

# =============================================================================
# Frontmatter解析
# =============================================================================

# 必須フィールド
_REQUIRED_FIELDS = {"name", "description", "type"}


def parse_frontmatter(content: str) -> tuple[MemoryFileFrontmatter | None, str]:
    """
    YAML frontmatterを解析（PyYAML不使用）

    --- で囲まれたブロックからkey: valueを抽出。
    必須フィールド（name, description, type）が揃っていない場合はNoneを返す。

    Args:
        content: ファイル全文

    Returns:
        (frontmatter, body) のタプル。
        frontmatterが無効な場合は (None, content) を返す。

    Example:
        >>> fm, body = parse_frontmatter("---\\nname: test\\ndescription: d\\ntype: user\\n---\\nbody")
        >>> fm["name"]
        'test'
    """
    # --- で始まるか確認
    if not content.startswith("---"):
        return None, content

    # 2つ目の --- を探す（最初の改行以降から）
    first_newline = content.find("\n")
    if first_newline == -1:
        return None, content

    second_delimiter = content.find("\n---", first_newline)
    if second_delimiter == -1:
        return None, content

    # frontmatterブロックを抽出
    fm_block = content[first_newline + 1 : second_delimiter]
    # body = 2つ目の --- の次の行以降
    body_start = content.find("\n", second_delimiter + 1)
    body = "" if body_start == -1 else content[body_start + 1 :]

    # key: value ペアを抽出
    fields: dict[str, str] = {}
    for line in fm_block.splitlines():
        line = line.strip()
        if not line:
            continue
        # 最初のコロンで分割（値にコロンを含む場合に対応）
        colon_pos = line.find(":")
        if colon_pos == -1:
            continue
        key = line[:colon_pos].strip()
        value = line[colon_pos + 1 :].strip()
        fields[key] = value

    # 必須フィールドの検証
    if not _REQUIRED_FIELDS.issubset(fields.keys()):
        return None, content

    # type値の検証
    if fields["type"] not in VALID_MEMORY_TYPES:
        return None, content

    frontmatter: MemoryFileFrontmatter = {
        "name": fields["name"],
        "description": fields["description"],
        "type": fields["type"],  # type: ignore[typeddict-item]
    }
    return frontmatter, body


# =============================================================================
# メモリファイル読み込み
# =============================================================================


def read_memory_file(file_path: Path) -> MemoryFile | None:
    """
    auto-memoryファイルを読み込みパースする

    frontmatterが無効なファイル（.consolidate-lock等）はNoneを返す。

    Args:
        file_path: メモリファイルのパス

    Returns:
        MemoryFile辞書。無効な場合はNone。
    """
    if not file_path.exists():
        return None

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    frontmatter, body = parse_frontmatter(content)
    if frontmatter is None:
        return None

    return MemoryFile(
        filename=file_path.name,
        path=str(file_path),
        frontmatter=frontmatter,
    )


# =============================================================================
# MEMORY.md インデックス読み込み
# =============================================================================

# [title](filename.md) 形式のリンクからファイル名を抽出
_LINK_PATTERN = re.compile(r"\[.*?\]\(([^)]+\.md)\)")


def read_memory_index(index_path: Path) -> MemoryIndex:
    """
    MEMORY.md（インデックスファイル）を読み込みパースする

    セクションヘッダ（## ）でグループ分けし、
    各セクション内のマークダウンリンクからファイル名を抽出。

    Args:
        index_path: MEMORY.mdのパス

    Returns:
        MemoryIndex辞書
    """
    try:
        raw_content = index_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return MemoryIndex(
            path=str(index_path),
            sections={},
        )

    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for line in raw_content.splitlines():
        # セクションヘッダ検出
        if line.startswith("## "):
            current_section = line[3:].strip()
            if current_section not in sections:
                sections[current_section] = []
            continue

        # リンクからファイル名を抽出
        if current_section is not None:
            for match in _LINK_PATTERN.finditer(line):
                sections[current_section].append(match.group(1))

    return MemoryIndex(
        path=str(index_path),
        sections=sections,
    )
