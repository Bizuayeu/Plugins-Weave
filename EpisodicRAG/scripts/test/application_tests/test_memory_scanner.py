#!/usr/bin/env python3
"""
application/auto_dream/memory_scanner.py のテスト
================================================

MemoryScannerの統合テスト。
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from application.auto_dream.memory_scanner import MemoryScanner


def _create_memory_env(base: Path, project_name: str = "test-project") -> Path:
    """テスト用メモリ環境を構築"""
    memory_dir = base / ".claude" / "projects" / project_name / "memory"
    memory_dir.mkdir(parents=True)

    # MEMORY.md
    (memory_dir / "MEMORY.md").write_text(
        "# Memory Index\n\n## User\n- [Profile](user_profile.md) — desc\n\n"
        "## Feedback\n- [Bias](feedback_bias.md) — desc\n",
        encoding="utf-8",
    )

    # メモリファイル
    (memory_dir / "user_profile.md").write_text(
        "---\nname: ユーザープロファイル\ndescription: テスト用\ntype: user\n---\n\n## 内容\nテスト",
        encoding="utf-8",
    )
    (memory_dir / "feedback_bias.md").write_text(
        "---\nname: バイアス修正\ndescription: テスト用フィードバック\ntype: feedback\n---\n\n修正記録",
        encoding="utf-8",
    )

    return memory_dir


class TestMemoryScanner:
    """MemoryScannerの統合テスト"""

    @pytest.mark.integration
    def test_メモリなし環境でno_memory(self, tmp_path: Path) -> None:
        """メモリディレクトリなし → status="no_memory" """
        fake_base = tmp_path / ".claude" / "projects"
        # ディレクトリすら作らない

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        assert result["status"] == "no_memory"
        assert result["memory_dir"] is None
        assert result["file_count"] == 0

    @pytest.mark.integration
    def test_正常スキャンでok(self, tmp_path: Path) -> None:
        """メモリファイルを正しくスキャン"""
        _create_memory_env(tmp_path)
        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        assert result["status"] == "ok"
        assert result["file_count"] == 2
        assert result["project_path"] == "test-project"
        assert result["memory_index"] is not None
        assert "User" in result["memory_index"]["sections"]

    @pytest.mark.integration
    def test_file_countが正確(self, tmp_path: Path) -> None:
        """file_countがmemory_filesのlen()と一致"""
        _create_memory_env(tmp_path)
        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        assert result["file_count"] == len(result["memory_files"])

    @pytest.mark.integration
    def test_malformedファイルを含む環境(self, tmp_path: Path) -> None:
        """無効ファイルはスキップ、有効分のみ返す"""
        memory_dir = _create_memory_env(tmp_path)

        # frontmatterなしファイルを追加
        (memory_dir / "broken.md").write_text("No frontmatter here", encoding="utf-8")
        # ロックファイル（.md拡張子ではないので除外される）
        (memory_dir / ".consolidate-lock").write_text("12345", encoding="utf-8")

        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        assert result["status"] == "ok"
        # broken.mdはスキップ、user_profile.mdとfeedback_bias.mdのみ
        assert result["file_count"] == 2

    @pytest.mark.integration
    def test_空のメモリディレクトリ(self, tmp_path: Path) -> None:
        """MEMORY.mdのみ、他ファイルなし"""
        memory_dir = tmp_path / ".claude" / "projects" / "empty-project" / "memory"
        memory_dir.mkdir(parents=True)
        (memory_dir / "MEMORY.md").write_text("# Memory Index\n", encoding="utf-8")

        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        assert result["status"] == "ok"
        assert result["file_count"] == 0
        assert result["memory_files"] == []

    @pytest.mark.integration
    def test_project_path指定(self, tmp_path: Path) -> None:
        """project_pathを指定してスキャン"""
        _create_memory_env(tmp_path, project_name="C--Users-test-DEV")
        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner(project_path="C:\\Users\\test\\DEV")
            result = scanner.scan()

        assert result["status"] == "ok"
        assert result["project_path"] == "C--Users-test-DEV"

    @pytest.mark.integration
    def test_エラー時はerrorステータス(self, tmp_path: Path) -> None:
        """予期せぬエラー → status="error" """
        with patch(
            "application.auto_dream.memory_scanner.discover_memory_dirs",
            side_effect=PermissionError("Access denied"),
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        assert result["status"] == "error"
        assert "Access denied" in result["error"]

    @pytest.mark.integration
    def test_メモリファイルのfrontmatterが正確(self, tmp_path: Path) -> None:
        """各ファイルのfrontmatterが正しく読まれている"""
        _create_memory_env(tmp_path)
        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        types = {mf["frontmatter"]["type"] for mf in result["memory_files"]}
        assert "user" in types
        assert "feedback" in types

    @pytest.mark.integration
    def test_memory_filesにcontentキーが含まれない(self, tmp_path: Path) -> None:
        """v5.4.0軽量化: 各memory_fileから content/content_length が除外されている"""
        _create_memory_env(tmp_path)
        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        assert result["status"] == "ok"
        assert len(result["memory_files"]) > 0
        for mf in result["memory_files"]:
            assert "content" not in mf, (
                f"memory_file {mf['filename']} should not have 'content' key"
            )
            assert "content_length" not in mf, (
                f"memory_file {mf['filename']} should not have 'content_length' key"
            )

    @pytest.mark.integration
    def test_memory_indexにraw_contentキーが含まれない(self, tmp_path: Path) -> None:
        """v5.4.0軽量化: memory_indexから raw_content が除外されている"""
        _create_memory_env(tmp_path)
        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        assert result["status"] == "ok"
        assert result["memory_index"] is not None
        assert "raw_content" not in result["memory_index"]

    @pytest.mark.integration
    def test_memory_filesに必要キーのみ含まれる(self, tmp_path: Path) -> None:
        """v5.4.0軽量化: 各memory_fileは filename/path/frontmatter のみ持つ"""
        _create_memory_env(tmp_path)
        fake_base = tmp_path / ".claude" / "projects"

        with patch(
            "infrastructure.auto_dream.memory_discovery.get_claude_projects_base",
            return_value=fake_base,
        ):
            scanner = MemoryScanner()
            result = scanner.scan()

        expected_keys = {"filename", "path", "frontmatter"}
        for mf in result["memory_files"]:
            assert set(mf.keys()) == expected_keys, (
                f"memory_file should have only {expected_keys}, got {set(mf.keys())}"
            )
