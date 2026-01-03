"""Tests for adapters.file_constants module (Stage 6: TDD)."""

import pytest


class TestFileConstantsExist:
    """ファイル定数モジュールの存在確認テスト"""

    def test_file_constants_module_exists(self):
        """file_constantsモジュールが存在することを確認"""
        from adapters import file_constants

        assert file_constants is not None

    def test_default_json_filename(self):
        """DEFAULT_JSON_FILENAMEが正しく定義されていること"""
        from adapters.file_constants import DEFAULT_JSON_FILENAME

        assert DEFAULT_JSON_FILENAME == "ExpressionImages.json"

    def test_default_html_filename(self):
        """DEFAULT_HTML_FILENAMEが正しく定義されていること"""
        from adapters.file_constants import DEFAULT_HTML_FILENAME

        assert DEFAULT_HTML_FILENAME == "VisualExpressionUI.html"

    def test_default_template_filename(self):
        """DEFAULT_TEMPLATE_FILENAMEが正しく定義されていること"""
        from adapters.file_constants import DEFAULT_TEMPLATE_FILENAME

        assert DEFAULT_TEMPLATE_FILENAME == "VisualExpressionUI.template.html"

    def test_skills_dir_markers(self):
        """SKILLS_DIR_MARKERSが正しく定義されていること"""
        from adapters.file_constants import SKILLS_DIR_MARKERS

        assert "SKILL.md" in SKILLS_DIR_MARKERS
        assert "VisualExpressionUI.template.html" in SKILLS_DIR_MARKERS

    def test_skills_dir_env_var(self):
        """SKILLS_DIR_ENV_VARが正しく定義されていること"""
        from adapters.file_constants import SKILLS_DIR_ENV_VAR

        assert SKILLS_DIR_ENV_VAR == "VISUAL_EXPRESSION_SKILLS_DIR"


class TestFileHandlerUsesConstants:
    """FileHandlerが定数を使用していることを確認"""

    def test_file_handler_uses_constant_for_json(self, tmp_path):
        """write_jsonのデフォルトがDEFAULT_JSON_FILENAMEと一致"""
        from adapters.file_constants import DEFAULT_JSON_FILENAME
        from adapters.file_handler import FileHandler

        handler = FileHandler(output_dir=str(tmp_path))
        path = handler.write_json({"test": "data"})

        assert path.name == DEFAULT_JSON_FILENAME

    def test_file_handler_uses_constant_for_html(self, tmp_path):
        """write_htmlのデフォルトがDEFAULT_HTML_FILENAMEと一致"""
        from adapters.file_constants import DEFAULT_HTML_FILENAME
        from adapters.file_handler import FileHandler

        handler = FileHandler(output_dir=str(tmp_path))
        path = handler.write_html("<html></html>")

        assert path.name == DEFAULT_HTML_FILENAME


class TestMaxSearchDepth:
    """MAX_SEARCH_DEPTH定数のテスト"""

    def test_max_search_depth_exists(self):
        """MAX_SEARCH_DEPTHが定義されていること"""
        from adapters.file_constants import MAX_SEARCH_DEPTH

        assert MAX_SEARCH_DEPTH is not None

    def test_max_search_depth_is_positive_integer(self):
        """MAX_SEARCH_DEPTHが正の整数であること"""
        from adapters.file_constants import MAX_SEARCH_DEPTH

        assert isinstance(MAX_SEARCH_DEPTH, int)
        assert MAX_SEARCH_DEPTH > 0

    def test_max_search_depth_is_reasonable(self):
        """MAX_SEARCH_DEPTHが妥当な範囲（5-20）であること"""
        from adapters.file_constants import MAX_SEARCH_DEPTH

        assert 5 <= MAX_SEARCH_DEPTH <= 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
