#!/usr/bin/env python3
"""
infrastructure/auto_dream/memory_discovery.py のテスト
====================================================

auto-memoryディレクトリ発見のテスト。
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from infrastructure.auto_dream.memory_discovery import (
    discover_memory_dirs,
    encode_project_path,
    get_claude_projects_base,
)


# =============================================================================
# encode_project_path テスト
# =============================================================================


class TestEncodeProjectPath:
    """プロジェクトパスエンコードのテスト"""

    @pytest.mark.unit
    def test_windowsパス(self) -> None:
        """C:\\Users\\anyth\\DEV → C--Users-anyth-DEV"""
        result = encode_project_path("C:\\Users\\anyth\\DEV")
        assert result == "C--Users-anyth-DEV"

    @pytest.mark.unit
    def test_unixパス(self) -> None:
        """/home/user/project → -home-user-project"""
        result = encode_project_path("/home/user/project")
        assert result == "-home-user-project"

    @pytest.mark.unit
    def test_ドライブレターのコロンが除去される(self) -> None:
        """C: のコロンが消える"""
        result = encode_project_path("C:\\")
        assert ":" not in result

    @pytest.mark.unit
    def test_混合パス区切り(self) -> None:
        """バックスラッシュとフォワードスラッシュの混在"""
        result = encode_project_path("C:\\Users/anyth\\DEV")
        assert result == "C--Users-anyth-DEV"

    @pytest.mark.unit
    def test_空文字列(self) -> None:
        """空のパスは空文字列"""
        result = encode_project_path("")
        assert result == ""


# =============================================================================
# get_claude_projects_base テスト
# =============================================================================


class TestGetClaudeProjectsBase:
    """Claudeプロジェクトベースパスのテスト"""

    @pytest.mark.unit
    def test_パスにclaude_projectsを含む(self) -> None:
        """戻り値が.claude/projectsを含む"""
        result = get_claude_projects_base()
        assert ".claude" in str(result)
        assert "projects" in str(result)

    @pytest.mark.unit
    def test_ホームディレクトリを展開(self) -> None:
        """Path.home()から始まるパスを返す"""
        result = get_claude_projects_base()
        assert str(result).startswith(str(Path.home()))


# =============================================================================
# discover_memory_dirs テスト
# =============================================================================


class TestDiscoverMemoryDirs:
    """メモリディレクトリ発見のテスト"""

    @pytest.mark.integration
    def test_メモリディレクトリが存在しない場合(self, tmp_path: Path) -> None:
        """~/.claude/projects/が存在しない → 空リスト"""
        fake_base = tmp_path / ".claude" / "projects"
        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = discover_memory_dirs()
        assert result == []

    @pytest.mark.integration
    def test_メモリディレクトリが存在する場合(self, tmp_path: Path) -> None:
        """MEMORY.mdがあるディレクトリを発見"""
        fake_base = tmp_path / ".claude" / "projects"
        memory_dir = fake_base / "C--Users-anyth-DEV" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("# Memory Index", encoding="utf-8")

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = discover_memory_dirs()

        assert len(result) == 1
        assert result[0] == memory_dir

    @pytest.mark.integration
    def test_project_path指定で正確に発見(self, tmp_path: Path) -> None:
        """--project-pathでエンコードして直接チェック"""
        fake_base = tmp_path / ".claude" / "projects"
        memory_dir = fake_base / "C--Users-anyth-DEV" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("# Memory Index", encoding="utf-8")

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = discover_memory_dirs(project_path="C:\\Users\\anyth\\DEV")

        assert len(result) == 1
        assert result[0] == memory_dir

    @pytest.mark.integration
    def test_project_path指定で存在しない場合(self, tmp_path: Path) -> None:
        """指定パスにメモリなし → 空リスト"""
        fake_base = tmp_path / ".claude" / "projects"
        fake_base.mkdir(parents=True)

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = discover_memory_dirs(project_path="C:\\nonexistent")

        assert result == []

    @pytest.mark.integration
    def test_MEMORY_md無しのディレクトリは除外(self, tmp_path: Path) -> None:
        """memory/ディレクトリはあるがMEMORY.mdがない → 除外"""
        fake_base = tmp_path / ".claude" / "projects"
        memory_dir = fake_base / "C--Users-anyth-DEV" / "memory"
        memory_dir.mkdir(parents=True)
        # MEMORY.md は作成しない

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = discover_memory_dirs()

        assert result == []

    @pytest.mark.integration
    def test_複数プロジェクトのメモリを発見(self, tmp_path: Path) -> None:
        """複数プロジェクトのメモリを全発見"""
        fake_base = tmp_path / ".claude" / "projects"
        for name in ["project-a", "project-b", "project-c"]:
            d = fake_base / name / "memory"
            d.mkdir(parents=True)
            (d / "MEMORY.md").write_text("# Memory", encoding="utf-8")

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = discover_memory_dirs()

        assert len(result) == 3
