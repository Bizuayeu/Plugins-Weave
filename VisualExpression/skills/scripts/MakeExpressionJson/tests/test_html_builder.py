"""Tests for usecases.html_builder module."""

import json
from pathlib import Path

import pytest

from usecases.html_builder import HtmlBuilder


class TestHtmlBuilderValidation:
    """Tests for HtmlBuilder input validation."""

    def test_rejects_missing_template(self):
        """存在しないテンプレートファイルはFileNotFoundErrorを発生"""
        with pytest.raises(FileNotFoundError):
            HtmlBuilder("/nonexistent/path/template.html")

    def test_rejects_template_without_placeholder(self, tmp_path):
        """プレースホルダーがないテンプレートはValueErrorを発生"""
        bad_template = tmp_path / "bad.html"
        bad_template.write_text("<html>no placeholder here</html>", encoding="utf-8")

        builder = HtmlBuilder(str(bad_template))
        with pytest.raises(ValueError, match="missing placeholder"):
            builder.load_template()

    def test_accepts_valid_template(self, sample_template_file):
        """有効なテンプレートファイルは受け入れる"""
        builder = HtmlBuilder(str(sample_template_file))
        content = builder.load_template()
        assert "__IMAGES_PLACEHOLDER__" in content


class TestHtmlBuilderFunctionality:
    """Tests for HtmlBuilder core functionality."""

    def test_load_template_returns_content(self, sample_template_file):
        """load_templateはファイル内容を返す"""
        builder = HtmlBuilder(str(sample_template_file))
        content = builder.load_template()
        assert isinstance(content, str)
        assert len(content) > 0

    def test_build_replaces_placeholder(self, sample_template_file):
        """buildはプレースホルダーを置換する"""
        builder = HtmlBuilder(str(sample_template_file))
        result = builder.build({"normal": "data:image/jpeg;base64,abc123"})

        # JSON形式（ダブルクォート、コロン後にスペースあり）
        assert '"normal": "data:image/jpeg;base64,abc123"' in result
        assert "__IMAGES_PLACEHOLDER__" not in result

    def test_build_multiple_images(self, sample_template_file):
        """複数画像のビルド"""
        builder = HtmlBuilder(str(sample_template_file))
        images = {
            "normal": "data:image/jpeg;base64,normal123",
            "smile": "data:image/jpeg;base64,smile456",
        }
        result = builder.build(images)

        # JSON形式（ダブルクォート）
        assert '"normal":' in result
        assert '"smile":' in result

    def test_build_auto_loads_template(self, sample_template_file):
        """load_template()を呼ばずにbuild()しても動作する"""
        builder = HtmlBuilder(str(sample_template_file))
        # load_template()を呼ばずに直接build()
        result = builder.build({"normal": "test"})
        # JSON形式（ダブルクォート、コロン後にスペースあり）
        assert '"normal": "test"' in result

    def test_build_from_json(self, sample_template_file, tmp_path):
        """JSONファイルからのビルド"""
        # JSONファイルを作成
        json_file = tmp_path / "images.json"
        json_data = {"normal": "data:image/jpeg;base64,fromjson"}
        json_file.write_text(json.dumps(json_data), encoding="utf-8")

        builder = HtmlBuilder(str(sample_template_file))
        result = builder.build_from_json(str(json_file))

        # JSON形式（ダブルクォート、コロン後にスペースあり）
        assert '"normal": "data:image/jpeg;base64,fromjson"' in result


class TestJsonSerialization:
    """JSON直列化のテスト（TDD）"""

    def test_output_uses_double_quotes(self, sample_template_file):
        """出力がJSON形式（ダブルクォート）であること"""
        builder = HtmlBuilder(str(sample_template_file))
        result = builder.build({"normal": "data:image/jpeg;base64,abc"})

        # JSON形式のダブルクォートを使用
        assert '"normal"' in result, "キーはダブルクォートで囲まれるべき"
        assert "'normal'" not in result, "シングルクォートは使わない"

    def test_special_characters_escaped(self, sample_template_file):
        """特殊文字が適切にエスケープされること"""
        builder = HtmlBuilder(str(sample_template_file))
        # バックスラッシュを含むデータ
        result = builder.build({"test": "data\\with\\backslash"})

        # JSONエスケープが適用されている（\\は\\\\になる）
        assert "data\\\\with\\\\backslash" in result, "バックスラッシュはエスケープされるべき"


class TestCustomPlaceholder:
    """カスタムプレースホルダーのテスト（Stage 5: TDD）"""

    def test_default_placeholder_constant(self):
        """DEFAULT_PLACEHOLDERが定義されていることを確認"""
        assert HtmlBuilder.DEFAULT_PLACEHOLDER == "__IMAGES_PLACEHOLDER__"

    def test_placeholder_parameter_in_init(self):
        """placeholderパラメータがコンストラクタに存在することを確認"""
        import inspect

        sig = inspect.signature(HtmlBuilder.__init__)
        assert "placeholder" in sig.parameters

    def test_custom_placeholder_accepted(self, tmp_path):
        """カスタムプレースホルダーが使用できることを確認"""
        template = tmp_path / "custom.html"
        template.write_text("<html>{{CUSTOM_MARKER}}</html>", encoding="utf-8")

        builder = HtmlBuilder(str(template), placeholder="{{CUSTOM_MARKER}}")
        builder.load_template()
        result = builder.build({"test": "value"})

        assert "{{CUSTOM_MARKER}}" not in result
        assert '"test": "value"' in result

    def test_custom_placeholder_validation(self, tmp_path):
        """カスタムプレースホルダーがない場合はValueErrorを発生"""
        template = tmp_path / "wrong.html"
        template.write_text("<html>no custom placeholder</html>", encoding="utf-8")

        builder = HtmlBuilder(str(template), placeholder="{{MISSING}}")
        with pytest.raises(ValueError, match="missing placeholder"):
            builder.load_template()


class TestExplicitSerialization:
    """明示的シリアライゼーションのテスト（Stage 3: TDD）"""

    def test_build_explicit_serialization(self, sample_template_file):
        """JSONが明示的にシリアライズされることを確認"""
        builder = HtmlBuilder(str(sample_template_file))
        images = {"key1": "value1", "key2": "value2"}

        result = builder.build(images)

        # 各ペアが正しくシリアライズされている
        assert '"key1"' in result
        assert '"key2"' in result
        assert '"value1"' in result
        assert '"value2"' in result

    def test_build_handles_special_chars_in_keys(self, sample_template_file):
        """キーに特殊文字を含む場合のエスケープを確認"""
        builder = HtmlBuilder(str(sample_template_file))
        images = {'key"with"quotes': "value"}

        result = builder.build(images)

        # キー内のダブルクォートが正しくエスケープされている
        assert r'key\"with\"quotes' in result

    def test_build_empty_dict(self, sample_template_file):
        """空の辞書でも正しく動作することを確認"""
        builder = HtmlBuilder(str(sample_template_file))

        result = builder.build({})

        assert "__IMAGES_PLACEHOLDER__" not in result

    def test_build_preserves_unicode(self, sample_template_file):
        """Unicode文字が保持されることを確認"""
        builder = HtmlBuilder(str(sample_template_file))
        images = {"smile": "日本語テスト"}

        result = builder.build(images)

        # Unicode文字がそのまま保持される（エスケープされない）
        assert "日本語テスト" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
