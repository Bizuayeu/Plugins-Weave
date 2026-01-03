"""Tests for adapters.file_handler and adapters.file_writer modules.

Note: Skills directory location tests have been moved to test_skills_locator.py.
This file focuses on FileWriter (file I/O) functionality.
"""

import json
from pathlib import Path

import pytest

from adapters.file_handler import FileHandler
from adapters.file_writer import FileWriter
from adapters.skills_locator import SkillsLocator


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
    """Tests for FileHandler path operations using SkillsLocator."""

    def test_get_skills_dir_returns_skills_folder(self):
        """SkillsLocator.get_skills_dirは'skills'フォルダを返す"""
        locator = SkillsLocator()

        result = locator.get_skills_dir()

        assert result.name == "skills"
        assert result.exists()

    def test_get_default_template_path_exists(self):
        """SkillsLocator.get_default_template_pathは存在するテンプレートパスを返す"""
        locator = SkillsLocator()

        result = locator.get_default_template_path()

        assert result.name == "VisualExpressionUI.template.html"
        assert result.exists()

    def test_read_template_returns_content(self):
        """FileWriter.read_templateはテンプレート内容を返す"""
        writer = FileWriter()
        locator = SkillsLocator()
        template_path = locator.get_default_template_path()

        content = writer.read_template(str(template_path))

        assert isinstance(content, str)
        assert len(content) > 0
        assert "__IMAGES_PLACEHOLDER__" in content


class TestSkillsDirDiscovery:
    """skills_dirパラメータと探索ロジックのテスト（SkillsLocator使用）"""

    def test_explicit_skills_dir_parameter(self, tmp_path):
        """skills_dirパラメータで明示指定できること"""
        locator = SkillsLocator(skills_dir=str(tmp_path))
        assert locator.get_skills_dir() == tmp_path

    def test_skills_dir_overrides_auto_detection(self, tmp_path):
        """skills_dirが指定されると自動検出より優先されること"""
        custom_dir = tmp_path / "custom_skills"
        custom_dir.mkdir()
        locator = SkillsLocator(skills_dir=str(custom_dir))

        result = locator.get_skills_dir()

        assert result == custom_dir
        assert result.name == "custom_skills"

    def test_fallback_returns_path(self):
        """マーカー未発見時もPathを返すこと（フォールバック動作）"""
        locator = SkillsLocator()
        result = locator.get_skills_dir()

        assert isinstance(result, Path)
        assert result.exists()


class TestSkillsDirEnvironmentVariable:
    """環境変数 VISUAL_EXPRESSION_SKILLS_DIR のテスト（SkillsLocator使用）"""

    def test_get_skills_dir_uses_env_var(self, tmp_path, monkeypatch):
        """環境変数 VISUAL_EXPRESSION_SKILLS_DIR が優先されることを確認"""
        skills_dir = tmp_path / "custom_skills"
        skills_dir.mkdir()
        monkeypatch.setenv("VISUAL_EXPRESSION_SKILLS_DIR", str(skills_dir))

        locator = SkillsLocator()

        result = locator.get_skills_dir()

        assert result == skills_dir

    def test_get_skills_dir_ignores_nonexistent_env_var(self, monkeypatch):
        """存在しないパスの環境変数は無視されることを確認"""
        monkeypatch.setenv("VISUAL_EXPRESSION_SKILLS_DIR", "/nonexistent/path")
        locator = SkillsLocator()

        # Should fall back to marker search
        result = locator.get_skills_dir()
        assert result != Path("/nonexistent/path")
        assert result.exists()

    def test_get_skills_dir_explicit_overrides_env(self, tmp_path, monkeypatch):
        """明示的引数が環境変数より優先されることを確認"""
        explicit_dir = tmp_path / "explicit"
        explicit_dir.mkdir()
        env_dir = tmp_path / "env"
        env_dir.mkdir()

        monkeypatch.setenv("VISUAL_EXPRESSION_SKILLS_DIR", str(env_dir))
        locator = SkillsLocator(skills_dir=str(explicit_dir))

        result = locator.get_skills_dir()
        assert result == explicit_dir

    def test_env_var_priority_order(self, tmp_path, monkeypatch):
        """優先順位: 明示的引数 > 環境変数 > 自動検出"""
        # 環境変数のみ設定
        env_dir = tmp_path / "from_env"
        env_dir.mkdir()
        monkeypatch.setenv("VISUAL_EXPRESSION_SKILLS_DIR", str(env_dir))

        locator_with_env = SkillsLocator()
        assert locator_with_env.get_skills_dir() == env_dir

        # 明示的引数を設定（環境変数より優先）
        explicit_dir = tmp_path / "explicit"
        explicit_dir.mkdir()
        locator_with_explicit = SkillsLocator(skills_dir=str(explicit_dir))
        assert locator_with_explicit.get_skills_dir() == explicit_dir


class TestGetSkillsDirDocstring:
    """SkillsLocator.get_skills_dir のdocstring存在テスト"""

    def test_get_skills_dir_has_docstring(self):
        """get_skills_dir に docstring が存在すること"""
        assert SkillsLocator.get_skills_dir.__doc__ is not None

    def test_get_skills_dir_docstring_contains_priority(self):
        """docstring に Priority 順序が記載されていること"""
        docstring = SkillsLocator.get_skills_dir.__doc__
        assert "Priority" in docstring

    def test_get_skills_dir_docstring_describes_env_var(self):
        """docstring に環境変数の説明が含まれること"""
        docstring = SkillsLocator.get_skills_dir.__doc__
        assert "VISUAL_EXPRESSION_SKILLS_DIR" in docstring

    def test_get_skills_dir_docstring_describes_all_fallbacks(self):
        """docstring に全フォールバック手段が記載されていること"""
        docstring = SkillsLocator.get_skills_dir.__doc__
        # 4つの優先順位が記載されている
        assert "1." in docstring
        assert "2." in docstring
        assert "3." in docstring
        assert "4." in docstring


class TestEnsureDirFunction:
    """ensure_dir ユーティリティ関数のテスト"""

    def test_ensure_dir_creates_new_directory(self, tmp_path):
        """新しいディレクトリを作成できること"""
        from adapters.file_handler import ensure_dir

        new_dir = tmp_path / "new_directory"
        result = ensure_dir(new_dir)

        assert result.exists()
        assert result.is_dir()
        assert result == new_dir

    def test_ensure_dir_handles_existing_directory(self, tmp_path):
        """既存ディレクトリでエラーにならないこと"""
        from adapters.file_handler import ensure_dir

        existing = tmp_path / "existing"
        existing.mkdir()

        result = ensure_dir(existing)

        assert result.exists()
        assert result == existing

    def test_ensure_dir_creates_parent_directories(self, tmp_path):
        """親ディレクトリも再帰的に作成されること"""
        from adapters.file_handler import ensure_dir

        deep_path = tmp_path / "a" / "b" / "c"
        result = ensure_dir(deep_path)

        assert result.exists()
        assert (tmp_path / "a" / "b").exists()

    def test_ensure_dir_returns_path(self, tmp_path):
        """Pathオブジェクトを返すこと"""
        from adapters.file_handler import ensure_dir

        result = ensure_dir(tmp_path / "test")

        assert isinstance(result, Path)


class TestBackwardCompatibility:
    """FileHandler後方互換性のテスト"""

    def test_file_handler_is_alias_for_file_writer(self):
        """FileHandlerはFileWriterのエイリアス"""
        assert FileHandler is FileWriter

    def test_file_handler_from_file_handler_module(self):
        """file_handlerモジュールからFileHandlerをインポートできる"""
        from adapters.file_handler import FileHandler as FH

        assert FH is FileWriter


class TestFileHandlerDeprecation:
    """file_handlerモジュールの非推奨警告テスト"""

    def test_import_file_handler_shows_deprecation_warning(self):
        """file_handlerからのimportで非推奨警告が出ること"""
        import importlib
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # 警告をトリガーするためにモジュールをリロード
            import adapters.file_handler as fh

            importlib.reload(fh)

            # DeprecationWarningが発生することを確認
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1

    def test_deprecation_message_mentions_alternatives(self):
        """警告メッセージに代替モジュールが記載されていること"""
        import importlib
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            import adapters.file_handler as fh

            importlib.reload(fh)

            messages = [str(x.message) for x in w]
            combined = " ".join(messages)

            assert "file_writer" in combined or "skills_locator" in combined


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
