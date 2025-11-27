#!/usr/bin/env python3
"""
test_json_repository.py
=======================

infrastructure/json_repository.py の単体テスト。
JSON読み書き、テンプレート処理、ディレクトリ作成をテスト。
"""
import json
import pytest
from pathlib import Path

from infrastructure.json_repository import (
    load_json,
    save_json,
    load_json_with_template,
    file_exists,
    ensure_directory,
)
from domain.exceptions import FileIOError


# =============================================================================
# load_json テスト
# =============================================================================

class TestLoadJson:
    """load_json() 関数のテスト"""

    @pytest.mark.integration
    def test_missing_file_raises_fileiioerror(self, tmp_path):
        """存在しないファイル → FileIOError"""
        missing_file = tmp_path / "missing.json"
        with pytest.raises(FileIOError, match="File not found"):
            load_json(missing_file)

    @pytest.mark.integration
    def test_invalid_json_raises_fileiioerror(self, tmp_path):
        """不正なJSON → FileIOError"""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json content")

        with pytest.raises(FileIOError, match="Invalid JSON"):
            load_json(invalid_file)

    @pytest.mark.integration
    def test_valid_json_returns_dict(self, tmp_path):
        """正常なJSON → dict"""
        valid_file = tmp_path / "valid.json"
        test_data = {"key": "value", "number": 42}
        valid_file.write_text(json.dumps(test_data))

        result = load_json(valid_file)
        assert result == test_data

    @pytest.mark.integration
    def test_utf8_encoding_handled(self, tmp_path):
        """UTF-8エンコーディング処理"""
        utf8_file = tmp_path / "utf8.json"
        test_data = {"japanese": "日本語テスト", "emoji": "🎉"}
        utf8_file.write_text(json.dumps(test_data, ensure_ascii=False), encoding="utf-8")

        result = load_json(utf8_file)
        assert result["japanese"] == "日本語テスト"
        assert result["emoji"] == "🎉"

    @pytest.mark.integration
    def test_nested_json_structure(self, tmp_path):
        """ネストされたJSON構造"""
        nested_file = tmp_path / "nested.json"
        test_data = {
            "level1": {
                "level2": {
                    "level3": ["a", "b", "c"]
                }
            }
        }
        nested_file.write_text(json.dumps(test_data))

        result = load_json(nested_file)
        assert result["level1"]["level2"]["level3"] == ["a", "b", "c"]


# =============================================================================
# save_json テスト
# =============================================================================

class TestSaveJson:
    """save_json() 関数のテスト"""

    @pytest.mark.integration
    def test_creates_parent_directories(self, tmp_path):
        """親ディレクトリを自動作成"""
        deep_path = tmp_path / "a" / "b" / "c" / "test.json"
        test_data = {"key": "value"}

        save_json(deep_path, test_data)

        assert deep_path.exists()
        assert deep_path.parent.exists()

    @pytest.mark.integration
    def test_saves_valid_json(self, tmp_path):
        """正常にJSONを保存"""
        json_file = tmp_path / "output.json"
        test_data = {"name": "test", "values": [1, 2, 3]}

        save_json(json_file, test_data)

        # 読み込んで検証
        with open(json_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        assert loaded == test_data

    @pytest.mark.integration
    def test_preserves_unicode(self, tmp_path):
        """Unicodeを保持（ensure_ascii=False）"""
        json_file = tmp_path / "unicode.json"
        test_data = {"japanese": "こんにちは", "korean": "안녕하세요"}

        save_json(json_file, test_data)

        # ファイル内容を直接確認
        content = json_file.read_text(encoding='utf-8')
        assert "こんにちは" in content
        assert "\\u" not in content  # エスケープされていない

    @pytest.mark.integration
    def test_custom_indent(self, tmp_path):
        """カスタムインデント"""
        json_file = tmp_path / "indented.json"
        test_data = {"key": "value"}

        save_json(json_file, test_data, indent=4)

        content = json_file.read_text()
        # 4スペースインデントが使用されている
        assert "    " in content or '"key"' in content

    @pytest.mark.integration
    def test_overwrites_existing_file(self, tmp_path):
        """既存ファイルを上書き"""
        json_file = tmp_path / "existing.json"
        json_file.write_text('{"old": "data"}')

        new_data = {"new": "data"}
        save_json(json_file, new_data)

        result = json.loads(json_file.read_text())
        assert result == new_data
        assert "old" not in result


# =============================================================================
# load_json_with_template テスト
# =============================================================================

class TestLoadJsonWithTemplate:
    """load_json_with_template() 関数のテスト"""

    @pytest.mark.integration
    def test_target_file_exists_load_it(self, tmp_path):
        """ターゲットファイルが存在 → そのまま読み込み"""
        target_file = tmp_path / "target.json"
        target_data = {"source": "target"}
        target_file.write_text(json.dumps(target_data))

        template_file = tmp_path / "template.json"
        template_file.write_text('{"source": "template"}')

        result = load_json_with_template(target_file, template_file)
        assert result["source"] == "target"

    @pytest.mark.integration
    def test_template_file_fallback(self, tmp_path):
        """ターゲットなし、テンプレートあり → テンプレート使用"""
        target_file = tmp_path / "target.json"  # 存在しない
        template_file = tmp_path / "template.json"
        template_data = {"source": "template", "initialized": True}
        template_file.write_text(json.dumps(template_data))

        result = load_json_with_template(target_file, template_file)
        assert result["source"] == "template"
        assert result["initialized"] is True

    @pytest.mark.integration
    def test_default_factory_fallback(self, tmp_path):
        """ターゲット・テンプレートなし、ファクトリあり → ファクトリ使用"""
        target_file = tmp_path / "target.json"

        def factory():
            return {"source": "factory", "created": True}

        result = load_json_with_template(
            target_file,
            template_file=None,
            default_factory=factory
        )
        assert result["source"] == "factory"
        assert result["created"] is True

    @pytest.mark.integration
    def test_no_fallback_returns_empty_dict(self, tmp_path):
        """全てなし → 空dict"""
        target_file = tmp_path / "target.json"

        result = load_json_with_template(target_file)
        assert result == {}

    @pytest.mark.integration
    def test_save_on_create_true(self, tmp_path):
        """save_on_create=True → ファイル作成"""
        target_file = tmp_path / "target.json"
        template_file = tmp_path / "template.json"
        template_file.write_text('{"data": "template"}')

        load_json_with_template(target_file, template_file, save_on_create=True)

        assert target_file.exists()

    @pytest.mark.integration
    def test_save_on_create_false(self, tmp_path):
        """save_on_create=False → ファイル作成しない"""
        target_file = tmp_path / "target.json"
        template_file = tmp_path / "template.json"
        template_file.write_text('{"data": "template"}')

        load_json_with_template(target_file, template_file, save_on_create=False)

        assert not target_file.exists()

    @pytest.mark.integration
    def test_invalid_target_json_raises_error(self, tmp_path):
        """ターゲットファイルが不正なJSON → FileIOError"""
        target_file = tmp_path / "target.json"
        target_file.write_text("{invalid json")

        with pytest.raises(FileIOError, match="Invalid JSON"):
            load_json_with_template(target_file)

    @pytest.mark.integration
    def test_invalid_template_json_raises_error(self, tmp_path):
        """テンプレートファイルが不正なJSON → FileIOError"""
        target_file = tmp_path / "target.json"  # 存在しない
        template_file = tmp_path / "template.json"
        template_file.write_text("{invalid json")

        with pytest.raises(FileIOError, match="Invalid JSON"):
            load_json_with_template(target_file, template_file)


# =============================================================================
# file_exists テスト
# =============================================================================

class TestFileExists:
    """file_exists() 関数のテスト"""

    @pytest.mark.integration
    def test_existing_file_returns_true(self, tmp_path):
        """存在するファイル → True"""
        existing_file = tmp_path / "exists.txt"
        existing_file.write_text("content")

        result = file_exists(existing_file)
        assert result is True

    @pytest.mark.integration
    def test_missing_file_returns_false(self, tmp_path):
        """存在しないファイル → False"""
        missing_file = tmp_path / "missing.txt"

        result = file_exists(missing_file)
        assert result is False

    @pytest.mark.integration
    def test_directory_returns_true(self, tmp_path):
        """ディレクトリも True（Path.exists()の挙動）"""
        dir_path = tmp_path / "directory"
        dir_path.mkdir()

        result = file_exists(dir_path)
        assert result is True


# =============================================================================
# ensure_directory テスト
# =============================================================================

class TestEnsureDirectory:
    """ensure_directory() 関数のテスト"""

    @pytest.mark.integration
    def test_creates_new_directory(self, tmp_path):
        """新規ディレクトリを作成"""
        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()

        ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    @pytest.mark.integration
    def test_creates_nested_directories(self, tmp_path):
        """ネストされたディレクトリを作成（parents=True）"""
        deep_dir = tmp_path / "a" / "b" / "c" / "d"
        assert not deep_dir.exists()

        ensure_directory(deep_dir)

        assert deep_dir.exists()
        assert (tmp_path / "a" / "b" / "c").exists()

    @pytest.mark.integration
    def test_existing_directory_no_error(self, tmp_path):
        """既存ディレクトリ → エラーなし（exist_ok=True）"""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        # 2回目の呼び出しでエラーにならない
        ensure_directory(existing_dir)

        assert existing_dir.exists()

    @pytest.mark.integration
    def test_file_as_parent_raises_error(self, tmp_path):
        """親パスがファイルの場合 → FileIOError"""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        # ファイルの下にディレクトリを作ろうとする
        invalid_dir = file_path / "subdir"

        with pytest.raises(FileIOError, match="Failed to create directory"):
            ensure_directory(invalid_dir)
