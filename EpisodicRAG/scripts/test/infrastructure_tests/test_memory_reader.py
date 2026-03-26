#!/usr/bin/env python3
"""
infrastructure/auto_dream/memory_reader.py のテスト
==================================================

frontmatter解析、メモリファイル読み込み、インデックス解析のテスト。
"""

from pathlib import Path

import pytest

from infrastructure.auto_dream.memory_reader import (
    parse_frontmatter,
    read_memory_file,
    read_memory_index,
)

# =============================================================================
# parse_frontmatter テスト
# =============================================================================


class TestParseFrontmatter:
    """YAML frontmatter解析のテスト"""

    @pytest.mark.unit
    def test_正常なfrontmatterを解析(self) -> None:
        """標準的な---/name/description/type/---形式"""
        content = "---\nname: テスト\ndescription: テスト用メモリ\ntype: user\n---\n\n## 内容\nテスト"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert fm["name"] == "テスト"
        assert fm["description"] == "テスト用メモリ"
        assert fm["type"] == "user"
        assert "## 内容" in body

    @pytest.mark.unit
    def test_frontmatterなしのファイル(self) -> None:
        """---で始まらない → (None, content)"""
        content = "# Just a normal file\nNo frontmatter here."
        fm, body = parse_frontmatter(content)
        assert fm is None
        assert body == content

    @pytest.mark.unit
    def test_不完全なfrontmatter(self) -> None:
        """閉じ---がない → (None, content)"""
        content = "---\nname: テスト\ndescription: d\ntype: user\n"
        fm, body = parse_frontmatter(content)
        assert fm is None
        assert body == content

    @pytest.mark.unit
    def test_必須フィールド不足(self) -> None:
        """typeが欠落 → (None, content)"""
        content = "---\nname: テスト\ndescription: テスト用\n---\nbody"
        fm, body = parse_frontmatter(content)
        assert fm is None

    @pytest.mark.unit
    def test_無効なtype値(self) -> None:
        """type: invalid → (None, content)"""
        content = "---\nname: テスト\ndescription: d\ntype: invalid\n---\nbody"
        fm, body = parse_frontmatter(content)
        assert fm is None

    @pytest.mark.unit
    def test_typeフィールドの4種別(self) -> None:
        """user, feedback, project, referenceの全4種が有効"""
        for memory_type in ["user", "feedback", "project", "reference"]:
            content = f"---\nname: t\ndescription: d\ntype: {memory_type}\n---\nbody"
            fm, body = parse_frontmatter(content)
            assert fm is not None, f"type={memory_type} should be valid"
            assert fm["type"] == memory_type

    @pytest.mark.unit
    def test_日本語のname_description(self) -> None:
        """UTF-8日本語が保持される"""
        content = "---\nname: 大環主プロファイル\ndescription: 力場tokenizer認知、めぐる組CEO\ntype: user\n---\nbody"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert fm["name"] == "大環主プロファイル"
        assert "力場tokenizer" in fm["description"]

    @pytest.mark.unit
    def test_descriptionにコロンを含む値(self) -> None:
        """値にコロンがあっても最初のコロンで分割"""
        content = "---\nname: テスト\ndescription: L00420で発見：原点回帰\ntype: project\n---\nbody"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert fm["description"] == "L00420で発見：原点回帰"

    @pytest.mark.unit
    def test_空のbody(self) -> None:
        """frontmatter後にbodyが空"""
        content = "---\nname: t\ndescription: d\ntype: user\n---"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert body == ""

    @pytest.mark.unit
    def test_frontmatter内の空行は無視(self) -> None:
        """空行を含むfrontmatter"""
        content = "---\nname: t\n\ndescription: d\n\ntype: user\n---\nbody"
        fm, body = parse_frontmatter(content)
        assert fm is not None
        assert fm["name"] == "t"


# =============================================================================
# read_memory_file テスト
# =============================================================================


class TestReadMemoryFile:
    """メモリファイル読み込みのテスト"""

    @pytest.mark.integration
    def test_正常なメモリファイル読み込み(self, tmp_path: Path) -> None:
        """有効なfrontmatter付きファイルを読み込み"""
        f = tmp_path / "user_profile.md"
        f.write_text(
            "---\nname: テスト\ndescription: d\ntype: user\n---\n\n## 内容\nテスト本文",
            encoding="utf-8",
        )
        result = read_memory_file(f)
        assert result is not None
        assert result["filename"] == "user_profile.md"
        assert result["frontmatter"]["type"] == "user"
        assert "テスト本文" in result["content"]

    @pytest.mark.integration
    def test_frontmatterなしのファイルはNone(self, tmp_path: Path) -> None:
        """frontmatterなしファイル → None"""
        f = tmp_path / "no_frontmatter.md"
        f.write_text("# Just markdown", encoding="utf-8")
        result = read_memory_file(f)
        assert result is None

    @pytest.mark.integration
    def test_存在しないファイルはNone(self, tmp_path: Path) -> None:
        """存在しないパス → None"""
        result = read_memory_file(tmp_path / "nonexistent.md")
        assert result is None

    @pytest.mark.integration
    def test_content_lengthが正確(self, tmp_path: Path) -> None:
        """content_lengthがbody部分の文字数と一致"""
        body = "テスト内容です。\n二行目。"
        f = tmp_path / "test.md"
        f.write_text(
            f"---\nname: t\ndescription: d\ntype: feedback\n---\n{body}",
            encoding="utf-8",
        )
        result = read_memory_file(f)
        assert result is not None
        assert result["content_length"] == len(body)
        assert result["content_length"] == len(result["content"])

    @pytest.mark.integration
    def test_pathが絶対パス文字列(self, tmp_path: Path) -> None:
        """pathフィールドが絶対パス文字列"""
        f = tmp_path / "test.md"
        f.write_text("---\nname: t\ndescription: d\ntype: user\n---\nbody", encoding="utf-8")
        result = read_memory_file(f)
        assert result is not None
        assert str(tmp_path) in result["path"]


# =============================================================================
# read_memory_index テスト
# =============================================================================


class TestReadMemoryIndex:
    """MEMORY.mdインデックス解析のテスト"""

    @pytest.mark.integration
    def test_正常なMEMORY_md解析(self, tmp_path: Path) -> None:
        """標準的なインデックスを読み込み"""
        content = """# Memory Index

## User
- [大環主プロファイル](user_profile.md) — 説明

## Feedback
- [テキスト知性バイアス](feedback_text_bias.md) — 説明
- [対話スタイル](feedback_interaction.md) — 説明
"""
        f = tmp_path / "MEMORY.md"
        f.write_text(content, encoding="utf-8")
        result = read_memory_index(f)
        assert "User" in result["sections"]
        assert "Feedback" in result["sections"]

    @pytest.mark.integration
    def test_セクション分割(self, tmp_path: Path) -> None:
        """4セクションに正しく分割"""
        content = """# Memory Index

## User
- [u](user.md)

## Feedback
- [f](feedback.md)

## Projects
- [p](project.md)

## References
- [r](ref.md)
"""
        f = tmp_path / "MEMORY.md"
        f.write_text(content, encoding="utf-8")
        result = read_memory_index(f)
        assert len(result["sections"]) == 4
        assert set(result["sections"].keys()) == {"User", "Feedback", "Projects", "References"}

    @pytest.mark.integration
    def test_リンクからファイル名を抽出(self, tmp_path: Path) -> None:
        """[name](file.md)形式からfile.mdを抽出"""
        content = """## User
- [Profile](user_profile.md) — desc
- [Other](other_user.md) — desc
"""
        f = tmp_path / "MEMORY.md"
        f.write_text(content, encoding="utf-8")
        result = read_memory_index(f)
        assert result["sections"]["User"] == ["user_profile.md", "other_user.md"]

    @pytest.mark.integration
    def test_空のMEMORY_md(self, tmp_path: Path) -> None:
        """空ファイル → 空sections"""
        f = tmp_path / "MEMORY.md"
        f.write_text("", encoding="utf-8")
        result = read_memory_index(f)
        assert result["sections"] == {}

    @pytest.mark.integration
    def test_raw_contentが保持される(self, tmp_path: Path) -> None:
        """元テキストがraw_contentに保持"""
        content = "# Memory\n## User\n- [u](u.md)"
        f = tmp_path / "MEMORY.md"
        f.write_text(content, encoding="utf-8")
        result = read_memory_index(f)
        assert result["raw_content"] == content

    @pytest.mark.integration
    def test_存在しないファイル(self, tmp_path: Path) -> None:
        """存在しないパス → 空結果"""
        result = read_memory_index(tmp_path / "nonexistent.md")
        assert result["sections"] == {}
        assert result["raw_content"] == ""
