"""Tests for adapters.file_handler module."""

import json
from pathlib import Path

import pytest

from adapters.file_handler import FileHandler


class TestFileHandlerDirectoryOperations:
    """Tests for FileHandler directory operations."""

    def test_ensure_output_dir_creates_directory(self, tmp_path):
        """ensure_output_dirは新しいディレクトリを作成する"""
        new_dir = tmp_path / "new_output_dir"
        handler = FileHandler(str(new_dir))

        result = handler.ensure_output_dir()

        assert result.exists()
        assert result.is_dir()

    def test_ensure_output_dir_uses_existing(self, tmp_path):
        """ensure_output_dirは既存ディレクトリを再利用する"""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        handler = FileHandler(str(existing_dir))

        result = handler.ensure_output_dir()

        assert result.exists()
        assert result == existing_dir


class TestFileHandlerWriteOperations:
    """Tests for FileHandler write operations."""

    def test_write_json_creates_file(self, tmp_path):
        """write_jsonはJSONファイルを作成する"""
        handler = FileHandler(str(tmp_path))
        data = {"test": "value", "number": 42}

        result = handler.write_json(data, "test.json")

        assert result.exists()
        assert result.name == "test.json"

    def test_write_json_content_is_valid(self, tmp_path):
        """write_jsonの内容は有効なJSON"""
        handler = FileHandler(str(tmp_path))
        data = {"key": "value", "nested": {"a": 1}}

        result = handler.write_json(data)
        content = json.loads(result.read_text(encoding="utf-8"))

        assert content == data

    def test_write_json_uses_default_filename(self, tmp_path):
        """write_jsonはデフォルトファイル名を使用"""
        handler = FileHandler(str(tmp_path))

        result = handler.write_json({"test": True})

        assert result.name == "ExpressionImages.json"

    def test_write_html_creates_file(self, tmp_path):
        """write_htmlはHTMLファイルを作成する"""
        handler = FileHandler(str(tmp_path))
        content = "<html><body>Test</body></html>"

        result = handler.write_html(content, "test.html")

        assert result.exists()
        assert result.name == "test.html"

    def test_write_html_content_matches(self, tmp_path):
        """write_htmlの内容は入力と一致"""
        handler = FileHandler(str(tmp_path))
        content = "<html><body>日本語テスト</body></html>"

        result = handler.write_html(content)
        saved_content = result.read_text(encoding="utf-8")

        assert saved_content == content


class TestFileHandlerPathOperations:
    """Tests for FileHandler path operations."""

    def test_get_skills_dir_returns_skills_folder(self):
        """get_skills_dirは'skills'フォルダを返す"""
        handler = FileHandler()

        result = handler.get_skills_dir()

        assert result.name == "skills"
        assert result.exists()

    def test_get_default_template_path_exists(self):
        """get_default_template_pathは存在するテンプレートパスを返す"""
        handler = FileHandler()

        result = handler.get_default_template_path()

        assert result.name == "VisualExpressionUI.template.html"
        assert result.exists()

    def test_read_template_returns_content(self):
        """read_templateはテンプレート内容を返す"""
        handler = FileHandler()
        template_path = handler.get_default_template_path()

        content = handler.read_template(str(template_path))

        assert isinstance(content, str)
        assert len(content) > 0
        assert "__IMAGES_PLACEHOLDER__" in content


class TestSkillsDirDiscovery:
    """skills_dirパラメータと探索ロジックのテスト（TDD）"""

    def test_explicit_skills_dir_parameter(self, tmp_path):
        """skills_dirパラメータで明示指定できること"""
        handler = FileHandler(skills_dir=str(tmp_path))
        assert handler.get_skills_dir() == tmp_path

    def test_skills_dir_overrides_auto_detection(self, tmp_path):
        """skills_dirが指定されると自動検出より優先されること"""
        custom_dir = tmp_path / "custom_skills"
        custom_dir.mkdir()
        handler = FileHandler(skills_dir=str(custom_dir))

        result = handler.get_skills_dir()

        assert result == custom_dir
        assert result.name == "custom_skills"

    def test_fallback_returns_path(self):
        """マーカー未発見時もPathを返すこと（フォールバック動作）"""
        handler = FileHandler()
        result = handler.get_skills_dir()

        assert isinstance(result, Path)
        assert result.exists()


class TestSkillsDirEnvironmentVariable:
    """環境変数 VISUAL_EXPRESSION_SKILLS_DIR のテスト（Stage 2: TDD）"""

    def test_get_skills_dir_uses_env_var(self, tmp_path, monkeypatch):
        """環境変数 VISUAL_EXPRESSION_SKILLS_DIR が優先されることを確認"""
        # Arrange
        skills_dir = tmp_path / "custom_skills"
        skills_dir.mkdir()
        monkeypatch.setenv("VISUAL_EXPRESSION_SKILLS_DIR", str(skills_dir))

        handler = FileHandler()

        # Act
        result = handler.get_skills_dir()

        # Assert
        assert result == skills_dir

    def test_get_skills_dir_ignores_nonexistent_env_var(self, monkeypatch):
        """存在しないパスの環境変数は無視されることを確認"""
        monkeypatch.setenv("VISUAL_EXPRESSION_SKILLS_DIR", "/nonexistent/path")
        handler = FileHandler()

        # Should fall back to marker search
        result = handler.get_skills_dir()
        assert result != Path("/nonexistent/path")
        assert result.exists()

    def test_get_skills_dir_explicit_overrides_env(self, tmp_path, monkeypatch):
        """明示的引数が環境変数より優先されることを確認"""
        explicit_dir = tmp_path / "explicit"
        explicit_dir.mkdir()
        env_dir = tmp_path / "env"
        env_dir.mkdir()

        monkeypatch.setenv("VISUAL_EXPRESSION_SKILLS_DIR", str(env_dir))
        handler = FileHandler(skills_dir=str(explicit_dir))

        result = handler.get_skills_dir()
        assert result == explicit_dir

    def test_env_var_priority_order(self, tmp_path, monkeypatch):
        """優先順位: 明示的引数 > 環境変数 > 自動検出"""
        # 環境変数のみ設定
        env_dir = tmp_path / "from_env"
        env_dir.mkdir()
        monkeypatch.setenv("VISUAL_EXPRESSION_SKILLS_DIR", str(env_dir))

        handler_with_env = FileHandler()
        assert handler_with_env.get_skills_dir() == env_dir

        # 明示的引数を設定（環境変数より優先）
        explicit_dir = tmp_path / "explicit"
        explicit_dir.mkdir()
        handler_with_explicit = FileHandler(skills_dir=str(explicit_dir))
        assert handler_with_explicit.get_skills_dir() == explicit_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
