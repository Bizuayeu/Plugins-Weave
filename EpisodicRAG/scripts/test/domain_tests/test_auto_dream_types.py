#!/usr/bin/env python3
"""
domain/auto_dream/types.py のユニットテスト
==========================================

Auto-Dream型定義の構造検証。
"""

import pytest

from domain.auto_dream.types import (
    VALID_MEMORY_TYPES,
    AutoDreamScanResult,
    MemoryFile,
    MemoryFileFrontmatter,
    MemoryIndex,
    MemoryType,
)

# =============================================================================
# MemoryType テスト
# =============================================================================


class TestMemoryType:
    """MemoryType Literal型の検証"""

    @pytest.mark.unit
    def test_4種別が定義されている(self) -> None:
        """user, feedback, project, referenceの4種"""
        assert VALID_MEMORY_TYPES == {"user", "feedback", "project", "reference"}

    @pytest.mark.unit
    def test_VALID_MEMORY_TYPESはset(self) -> None:
        """検証用セットがsetであること"""
        assert isinstance(VALID_MEMORY_TYPES, set)


# =============================================================================
# MemoryFileFrontmatter テスト
# =============================================================================


class TestMemoryFileFrontmatter:
    """MemoryFileFrontmatter TypedDictの検証"""

    @pytest.mark.unit
    def test_必須フィールドで構築可能(self) -> None:
        """name, description, typeの3フィールドで構築"""
        fm: MemoryFileFrontmatter = {
            "name": "テスト",
            "description": "テスト用メモリ",
            "type": "user",
        }
        assert fm["name"] == "テスト"
        assert fm["description"] == "テスト用メモリ"
        assert fm["type"] == "user"

    @pytest.mark.unit
    def test_日本語フィールド値(self) -> None:
        """日本語のname/descriptionが保持される"""
        fm: MemoryFileFrontmatter = {
            "name": "大環主プロファイル",
            "description": "力場tokenizer認知、めぐる組CEO、人機習合の対話相手",
            "type": "user",
        }
        assert "大環主" in fm["name"]
        assert "力場tokenizer" in fm["description"]


# =============================================================================
# MemoryFile テスト
# =============================================================================


class TestMemoryFile:
    """MemoryFile TypedDictの検証"""

    @pytest.mark.unit
    def test_必須フィールドで構築可能(self) -> None:
        """5フィールドで構築"""
        mf: MemoryFile = {
            "filename": "user_profile.md",
            "path": "/home/user/.claude/projects/X/memory/user_profile.md",
            "frontmatter": {
                "name": "テスト",
                "description": "説明",
                "type": "user",
            },
            "content": "## 内容\nテスト",
            "content_length": 10,
        }
        assert mf["filename"] == "user_profile.md"
        assert mf["content_length"] == 10

    @pytest.mark.unit
    def test_content_lengthはcontentの文字数と対応(self) -> None:
        """content_lengthがcontentのlen()と一致することを期待"""
        content = "テスト内容"
        mf: MemoryFile = {
            "filename": "test.md",
            "path": "/test.md",
            "frontmatter": {"name": "t", "description": "d", "type": "feedback"},
            "content": content,
            "content_length": len(content),
        }
        assert mf["content_length"] == len(mf["content"])


# =============================================================================
# MemoryIndex テスト
# =============================================================================


class TestMemoryIndex:
    """MemoryIndex TypedDictの検証"""

    @pytest.mark.unit
    def test_必須フィールドで構築可能(self) -> None:
        """path, sections, raw_contentの3フィールド"""
        mi: MemoryIndex = {
            "path": "/memory/MEMORY.md",
            "sections": {
                "User": ["user_profile.md"],
                "Feedback": ["feedback_text_bias.md"],
            },
            "raw_content": "# Memory Index\n...",
        }
        assert "User" in mi["sections"]
        assert mi["sections"]["User"] == ["user_profile.md"]

    @pytest.mark.unit
    def test_空のsections(self) -> None:
        """セクションが空でも構築可能"""
        mi: MemoryIndex = {
            "path": "/memory/MEMORY.md",
            "sections": {},
            "raw_content": "",
        }
        assert mi["sections"] == {}


# =============================================================================
# AutoDreamScanResult テスト
# =============================================================================


class TestAutoDreamScanResult:
    """AutoDreamScanResult TypedDictの検証"""

    @pytest.mark.unit
    def test_ok状態で構築可能(self) -> None:
        """status="ok"の完全な結果"""
        result: AutoDreamScanResult = {
            "status": "ok",
            "project_path": "C--Users-anyth-DEV",
            "memory_dir": "/home/.claude/projects/C--Users-anyth-DEV/memory",
            "memory_index": {
                "path": "/memory/MEMORY.md",
                "sections": {},
                "raw_content": "",
            },
            "memory_files": [],
            "file_count": 0,
            "error": None,
        }
        assert result["status"] == "ok"
        assert result["error"] is None

    @pytest.mark.unit
    def test_no_memory状態で構築可能(self) -> None:
        """status="no_memory"の結果"""
        result: AutoDreamScanResult = {
            "status": "no_memory",
            "project_path": None,
            "memory_dir": None,
            "memory_index": None,
            "memory_files": [],
            "file_count": 0,
            "error": None,
        }
        assert result["status"] == "no_memory"
        assert result["memory_dir"] is None

    @pytest.mark.unit
    def test_error状態で構築可能(self) -> None:
        """status="error"の結果"""
        result: AutoDreamScanResult = {
            "status": "error",
            "project_path": None,
            "memory_dir": None,
            "memory_index": None,
            "memory_files": [],
            "file_count": 0,
            "error": "ファイル読み込みエラー",
        }
        assert result["status"] == "error"
        assert "エラー" in result["error"]

    @pytest.mark.unit
    def test_statusの有効値(self) -> None:
        """ok, no_memory, errorの3値"""
        valid_statuses = {"ok", "no_memory", "error"}
        for status in valid_statuses:
            result: AutoDreamScanResult = {
                "status": status,
                "project_path": None,
                "memory_dir": None,
                "memory_index": None,
                "memory_files": [],
                "file_count": 0,
                "error": None,
            }
            assert result["status"] in valid_statuses
