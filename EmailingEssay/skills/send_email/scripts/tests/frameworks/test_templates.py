# tests/frameworks/test_templates.py
"""
テンプレートシステムのテスト
"""
import pytest
import sys
import os

# scriptsディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frameworks.templates import load_template, render_template, TemplateError


class TestLoadTemplate:
    """load_template() のテスト"""

    def test_load_existing_template(self):
        """存在するテンプレートのロード"""
        content = load_template("essay_waiter.py.template")
        assert "{{target_time}}" in content
        assert "{{claude_args}}" in content

    def test_load_nonexistent_template_raises_error(self):
        """存在しないテンプレートでエラー"""
        with pytest.raises(TemplateError):
            load_template("nonexistent.template")


class TestRenderTemplate:
    """render_template() のテスト"""

    def test_render_simple_template(self):
        """シンプルなテンプレートのレンダリング"""
        template = "Hello {{name}}, time is {{time}}"
        result = render_template(template, name="World", time="12:00")
        assert result == "Hello World, time is 12:00"

    def test_render_preserves_unmatched_placeholders(self):
        """マッチしないプレースホルダーは保持"""
        template = "Hello {{name}}, unknown is {{unknown}}"
        result = render_template(template, name="World")
        assert "{{unknown}}" in result

    def test_render_handles_special_characters(self):
        """特殊文字を含む値のレンダリング"""
        template = "Theme: {{theme}}"
        result = render_template(template, theme="朝の振り返り")
        assert result == "Theme: 朝の振り返り"
