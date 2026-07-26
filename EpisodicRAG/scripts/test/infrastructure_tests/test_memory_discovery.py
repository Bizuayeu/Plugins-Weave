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
    resolve_project_from_path,
)

# =============================================================================
# encode_project_path テスト
# =============================================================================


class TestEncodeProjectPath:
    """プロジェクトパスエンコードのテスト"""

    @pytest.mark.unit
    def test_windowsパス(self) -> None:
        """C:\\Users\\you\\DEV → C--Users-you-DEV"""
        result = encode_project_path("C:\\Users\\you\\DEV")
        assert result == "C--Users-you-DEV"

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
        result = encode_project_path("C:\\Users/you\\DEV")
        assert result == "C--Users-you-DEV"

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
        memory_dir = fake_base / "C--Users-you-DEV" / "memory"
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
        memory_dir = fake_base / "C--Users-you-DEV" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("# Memory Index", encoding="utf-8")

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = discover_memory_dirs(project_path="C:\\Users\\you\\DEV")

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
        memory_dir = fake_base / "C--Users-you-DEV" / "memory"
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


# =============================================================================
# resolve_project_from_path テスト
# =============================================================================


class TestResolveProjectFromPath:
    """base_dirからClaude Codeプロジェクトパスを逆引きするテスト

    resolve_project_from_pathはPath.resolve()で実パスへ正規化してから遡るため、
    テストのパスもOSネイティブに組み立てる（Windows形式の文字列を直書きすると
    POSIX上では1コンポーネントに潰れて成立しない）。
    """

    @staticmethod
    def _register(fake_base: Path, project_dir: Path) -> None:
        """project_dirをClaude Codeプロジェクトとしてfake_baseに登録する"""
        encoded = encode_project_path(str(project_dir.resolve()))
        memory_dir = fake_base / encoded / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("# Memory", encoding="utf-8")

    @pytest.mark.unit
    def test_完全一致でプロジェクトを発見(self, tmp_path: Path) -> None:
        """base_dirが直接プロジェクトパスの場合"""
        fake_base = tmp_path / ".claude" / "projects"
        project_dir = tmp_path / "workspace" / "DEV"
        project_dir.mkdir(parents=True)
        self._register(fake_base, project_dir)

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = resolve_project_from_path(str(project_dir))

        assert result is not None
        assert Path(result).name == "DEV"

    @pytest.mark.unit
    def test_祖先ディレクトリでプロジェクトを発見(self, tmp_path: Path) -> None:
        """base_dirの祖先にプロジェクトがある場合（本バグの核心ケース）"""
        fake_base = tmp_path / ".claude" / "projects"
        project_dir = tmp_path / "workspace" / "DEV"
        deep_dir = project_dir / "sub" / "deep"
        deep_dir.mkdir(parents=True)
        self._register(fake_base, project_dir)

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = resolve_project_from_path(str(deep_dir))

        assert result is not None
        assert Path(result).name == "DEV"

    @pytest.mark.unit
    def test_マッチなしでNone(self, tmp_path: Path) -> None:
        """どの祖先にもメモリがない場合"""
        fake_base = tmp_path / ".claude" / "projects"
        fake_base.mkdir(parents=True)

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = resolve_project_from_path(str(tmp_path / "nonexistent" / "path"))

        assert result is None

    @pytest.mark.unit
    def test_ルートまで遡って停止(self, tmp_path: Path) -> None:
        """無限ループしない（ルートで停止）"""
        fake_base = tmp_path / ".claude" / "projects"
        fake_base.mkdir(parents=True)

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = resolve_project_from_path(tmp_path.anchor)

        assert result is None

    @pytest.mark.unit
    def test_projects_base未存在でNone(self, tmp_path: Path) -> None:
        """~/.claude/projects/自体がない場合"""
        fake_base = tmp_path / "nonexistent"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            result = resolve_project_from_path(str(tmp_path / "workspace" / "DEV"))

        assert result is None
