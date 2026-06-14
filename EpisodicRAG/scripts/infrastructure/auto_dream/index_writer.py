#!/usr/bin/env python3
"""
Index Writer
============

dream-defrag（引く dream）の MEMORY.md live index 同期。

剪定後の決定論的 hygiene を担う: 既存 MEMORY.md を読み、**ディスク上に現存する
memory ファイル**に索引を同期する。生き残りエントリの行（タイトル・— 説明
one-liner 含む）は verbatim 保持し、ディスクから消えたエントリのリンク行のみ落とす。
セクションヘッダ・前文・空行など非エントリ行は保持する。

判断（何を剪定するか）は Claude=LLM が行い、実際の memory/*.md の削除・統合も
Claude が Edit で確定する。本 writer は「ディスクから消えたものを索引から外す」
決定論のみ——sections からのゼロ生成はしない（one-liner 説明を失うため）。

⚠️ 破壊的操作。auto-memory は git 非追跡なので、必ず snapshot 後にのみ apply すること。

Usage:
    from infrastructure.auto_dream.index_writer import rebuild_index_text, apply_index

    new_text = rebuild_index_text(memory_dir)   # プレビュー（書き込まない）
    apply_index(memory_dir, new_text)           # 書き戻し
"""

import re
from pathlib import Path

# [title](filename.md) のうち、リンク先が **パス区切りを含まない素のファイル名**
# のものだけを「メモリエントリ行」と見なす。/ や \ を含むパス・URL は対象外。
_ENTRY_LINK = re.compile(r"\[[^\]]*\]\(([^)/\\]+\.md)\)")

# MEMORY.md 自体はエントリではない
_INDEX_FILENAME = "MEMORY.md"


def _entry_target(line: str) -> "str | None":
    """行がメモリエントリ行なら、その素のファイル名を返す。違えば None。"""
    m = _ENTRY_LINK.search(line)
    if m is None:
        return None
    return m.group(1)


def _existing_memory_files(memory_dir: Path) -> set:
    """memory dir 直下に現存する *.md のファイル名集合（MEMORY.md 自体は除く）"""
    return {p.name for p in memory_dir.glob("*.md") if p.name != _INDEX_FILENAME}


def rebuild_index_text(memory_dir: Path) -> str:
    """
    既存 MEMORY.md を、ディスク現存の memory ファイルに同期したテキストを返す

    ディスクから消えたエントリのリンク行を落とすだけで、生き残りの行・
    セクション構造・前文は verbatim 保持する（書き込みはしない＝プレビュー）。

    Args:
        memory_dir: auto-memory ディレクトリ（MEMORY.md を含む）

    Returns:
        同期済み MEMORY.md テキスト

    Raises:
        FileNotFoundError: MEMORY.md が存在しない場合
    """
    index_path = memory_dir / _INDEX_FILENAME
    if not index_path.exists():
        raise FileNotFoundError(f"MEMORY.md not found: {index_path}")

    raw = index_path.read_text(encoding="utf-8")
    existing = _existing_memory_files(memory_dir)

    kept_lines = []
    for line in raw.splitlines():
        target = _entry_target(line)
        if target is not None and target not in existing:
            continue  # ディスクから消えたエントリ行は落とす
        kept_lines.append(line)

    text = "\n".join(kept_lines)
    # 元ファイルが末尾改行を持つなら維持
    if raw.endswith("\n"):
        text += "\n"
    return text


def apply_index(memory_dir: Path, text: str) -> Path:
    """
    同期済みテキストを MEMORY.md へ書き戻す（破壊的）

    ⚠️ 必ず snapshot 後にのみ呼ぶこと（auto-memory は git 非追跡で revert 不能）。

    Args:
        memory_dir: auto-memory ディレクトリ
        text: 書き込むテキスト（通常 rebuild_index_text の出力）

    Returns:
        書き込んだ MEMORY.md のパス
    """
    index_path = memory_dir / _INDEX_FILENAME
    index_path.write_text(text, encoding="utf-8")
    return index_path
