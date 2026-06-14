#!/usr/bin/env python3
"""
infrastructure/auto_dream/index_writer.py のテスト
================================================

MEMORY.md live index の決定論的同期（剪定後の hygiene）の検証。

設計: sections からゼロ生成せず、既存 index を読んでディスク現存 .md に
同期する。生き残りエントリの行（タイトル・— 説明 one-liner）は verbatim 保持し、
ディスクから消えたエントリの行のみ落とす。判断（何を消すか）は Claude、
本 writer は「消えたものを索引から外す」決定論のみ。
"""

from pathlib import Path

import pytest

from infrastructure.auto_dream.index_writer import rebuild_index_text
from infrastructure.auto_dream.memory_reader import read_memory_index

_INDEX = """# Memory Index

## User
- [プロファイル](user_profile.md) — 認知特性

## Feedback
- [バイアス](feedback_bias.md) — 学術偏重への校正
- [対話](feedback_interaction.md) — 簡潔・高コンテキスト
"""


def _build(base: Path, on_disk: list) -> Path:
    """MEMORY.md と on_disk のファイル群を構築して memory dir を返す"""
    memory_dir = base / "memory"
    memory_dir.mkdir(parents=True)
    (memory_dir / "MEMORY.md").write_text(_INDEX, encoding="utf-8")
    for name in on_disk:
        (memory_dir / name).write_text(
            "---\nname: n\ndescription: d\ntype: feedback\n---\nbody", encoding="utf-8"
        )
    return memory_dir


class TestRebuildIndexRoundTrip:
    """全ファイル現存時は構造を壊さない（round-trip）"""

    @pytest.mark.integration
    def test_index再生成がread_memory_indexとround_trip(self, tmp_path: Path) -> None:
        """全エントリがディスクに在れば、再生成→再パースで元 sections に一致"""
        memory_dir = _build(
            tmp_path,
            ["user_profile.md", "feedback_bias.md", "feedback_interaction.md"],
        )
        before = read_memory_index(memory_dir / "MEMORY.md")["sections"]

        new_text = rebuild_index_text(memory_dir)
        (memory_dir / "MEMORY.md").write_text(new_text, encoding="utf-8")
        after = read_memory_index(memory_dir / "MEMORY.md")["sections"]

        assert after == before


class TestRebuildIndexPrune:
    """ディスクから消えたエントリの行を落とす"""

    @pytest.mark.integration
    def test_削除されたファイルのエントリが落ちる(self, tmp_path: Path) -> None:
        """feedback_bias.md をディスクから外す → 索引からも消える"""
        memory_dir = _build(
            tmp_path,
            ["user_profile.md", "feedback_interaction.md"],  # feedback_bias.md なし
        )
        new_text = rebuild_index_text(memory_dir)

        assert "feedback_bias.md" not in new_text
        assert "user_profile.md" in new_text
        assert "feedback_interaction.md" in new_text

    @pytest.mark.integration
    def test_生存エントリのone_liner説明が保持される(self, tmp_path: Path) -> None:
        """生き残りの行は タイトル・— 説明 ごと verbatim 保持"""
        memory_dir = _build(
            tmp_path,
            ["user_profile.md", "feedback_interaction.md"],
        )
        new_text = rebuild_index_text(memory_dir)

        assert "認知特性" in new_text  # user_profile の説明
        assert "簡潔・高コンテキスト" in new_text  # feedback_interaction の説明
        assert "## User" in new_text  # セクションヘッダ保持
