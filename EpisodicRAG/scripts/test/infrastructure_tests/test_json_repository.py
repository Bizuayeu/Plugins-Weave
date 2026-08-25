#!/usr/bin/env python3
"""
test_json_repository.py
=======================

infrastructure/json_repository.py の単体テスト。
JSON読み書き、テンプレート処理、ディレクトリ作成をテスト。
"""

import json
from pathlib import Path

import pytest

from domain.exceptions import FileIOError
from infrastructure.json_repository import (
    confirm_file_overwrite,
    ensure_directory,
    file_exists,
    load_json,
    load_json_with_template,
    save_json,
    try_load_json,
    try_read_json_from_file,
)

# =============================================================================
# load_json テスト
# =============================================================================


class TestLoadJson:
    """load_json() 関数のテスト"""

    @pytest.mark.integration
    def test_missing_file_raises_fileiioerror(self, tmp_path: Path) -> None:
        """存在しないファイル → FileIOError"""
        missing_file = tmp_path / "missing.json"
        with pytest.raises(FileIOError, match="File not found"):
            load_json(missing_file)

    @pytest.mark.integration
    def test_invalid_json_raises_fileiioerror(self, tmp_path: Path) -> None:
        """不正なJSON → FileIOError"""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json content")

        with pytest.raises(FileIOError, match="Invalid JSON"):
            load_json(invalid_file)

    @pytest.mark.integration
    def test_valid_json_returns_dict(self, tmp_path: Path) -> None:
        """正常なJSON → dict"""
        valid_file = tmp_path / "valid.json"
        test_data = {"key": "value", "number": 42}
        valid_file.write_text(json.dumps(test_data))

        result = load_json(valid_file)
        assert result == test_data

    @pytest.mark.integration
    def test_utf8_encoding_handled(self, tmp_path: Path) -> None:
        """UTF-8エンコーディング処理"""
        utf8_file = tmp_path / "utf8.json"
        test_data = {"japanese": "日本語テスト", "emoji": "🎉"}
        utf8_file.write_text(
            json.dumps(test_data, ensure_ascii=False), encoding="utf-8"
        )

        result = load_json(utf8_file)
        assert result["japanese"] == "日本語テスト"
        assert result["emoji"] == "🎉"

    @pytest.mark.integration
    def test_nested_json_structure(self, tmp_path: Path) -> None:
        """ネストされたJSON構造"""
        nested_file = tmp_path / "nested.json"
        test_data = {"level1": {"level2": {"level3": ["a", "b", "c"]}}}
        nested_file.write_text(json.dumps(test_data))

        result = load_json(nested_file)
        assert result["level1"]["level2"]["level3"] == ["a", "b", "c"]


# =============================================================================
# save_json テスト
# =============================================================================


class TestSaveJson:
    """save_json() 関数のテスト"""

    @pytest.mark.integration
    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """親ディレクトリを自動作成"""
        deep_path = tmp_path / "a" / "b" / "c" / "test.json"
        test_data = {"key": "value"}

        save_json(deep_path, test_data)

        assert deep_path.exists()
        assert deep_path.parent.exists()

    @pytest.mark.integration
    def test_saves_valid_json(self, tmp_path: Path) -> None:
        """正常にJSONを保存"""
        json_file = tmp_path / "output.json"
        test_data = {"name": "test", "values": [1, 2, 3]}

        save_json(json_file, test_data)

        # 読み込んで検証
        with json_file.open(encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == test_data

    @pytest.mark.integration
    def test_preserves_unicode(self, tmp_path: Path) -> None:
        """Unicodeを保持（ensure_ascii=False）"""
        json_file = tmp_path / "unicode.json"
        test_data = {"japanese": "こんにちは", "korean": "안녕하세요"}

        save_json(json_file, test_data)

        # ファイル内容を直接確認
        content = json_file.read_text(encoding="utf-8")
        assert "こんにちは" in content
        assert "\\u" not in content  # エスケープされていない

    @pytest.mark.integration
    def test_custom_indent(self, tmp_path: Path) -> None:
        """カスタムインデント"""
        json_file = tmp_path / "indented.json"
        test_data = {"key": "value"}

        save_json(json_file, test_data, indent=4)

        content = json_file.read_text()
        # 4スペースインデントが使用されている
        assert "    " in content or '"key"' in content

    @pytest.mark.integration
    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
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
    def test_target_file_exists_load_it(self, tmp_path: Path) -> None:
        """ターゲットファイルが存在 → そのまま読み込み"""
        target_file = tmp_path / "target.json"
        target_data = {"source": "target"}
        target_file.write_text(json.dumps(target_data))

        template_file = tmp_path / "template.json"
        template_file.write_text('{"source": "template"}')

        result = load_json_with_template(target_file, template_file)
        assert result["source"] == "target"

    @pytest.mark.integration
    def test_template_file_fallback(self, tmp_path: Path) -> None:
        """ターゲットなし、テンプレートあり → テンプレート使用"""
        target_file = tmp_path / "target.json"  # 存在しない
        template_file = tmp_path / "template.json"
        template_data = {"source": "template", "initialized": True}
        template_file.write_text(json.dumps(template_data))

        result = load_json_with_template(target_file, template_file)
        assert result["source"] == "template"
        assert result["initialized"] is True

    @pytest.mark.integration
    def test_default_factory_fallback(self, tmp_path: Path):
        """ターゲット・テンプレートなし、ファクトリあり → ファクトリ使用"""
        target_file = tmp_path / "target.json"

        def factory():
            return {"source": "factory", "created": True}

        result = load_json_with_template(
            target_file, template_file=None, default_factory=factory
        )
        assert result["source"] == "factory"
        assert result["created"] is True

    @pytest.mark.integration
    def test_no_fallback_returns_empty_dict(self, tmp_path: Path) -> None:
        """全てなし → 空dict"""
        target_file = tmp_path / "target.json"

        result = load_json_with_template(target_file)
        assert result == {}

    @pytest.mark.integration
    def test_save_on_create_true(self, tmp_path: Path) -> None:
        """save_on_create=True → ファイル作成"""
        target_file = tmp_path / "target.json"
        template_file = tmp_path / "template.json"
        template_file.write_text('{"data": "template"}')

        load_json_with_template(target_file, template_file, save_on_create=True)

        assert target_file.exists()

    @pytest.mark.integration
    def test_save_on_create_false(self, tmp_path: Path) -> None:
        """save_on_create=False → ファイル作成しない"""
        target_file = tmp_path / "target.json"
        template_file = tmp_path / "template.json"
        template_file.write_text('{"data": "template"}')

        load_json_with_template(target_file, template_file, save_on_create=False)

        assert not target_file.exists()

    @pytest.mark.integration
    def test_invalid_target_json_raises_error(self, tmp_path: Path) -> None:
        """ターゲットファイルが不正なJSON → FileIOError"""
        target_file = tmp_path / "target.json"
        target_file.write_text("{invalid json")

        with pytest.raises(FileIOError, match="Invalid JSON"):
            load_json_with_template(target_file)

    @pytest.mark.integration
    def test_invalid_template_json_raises_error(self, tmp_path: Path) -> None:
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
    def test_existing_file_returns_true(self, tmp_path: Path) -> None:
        """存在するファイル → True"""
        existing_file = tmp_path / "exists.txt"
        existing_file.write_text("content")

        result = file_exists(existing_file)
        assert result is True

    @pytest.mark.integration
    def test_missing_file_returns_false(self, tmp_path: Path) -> None:
        """存在しないファイル → False"""
        missing_file = tmp_path / "missing.txt"

        result = file_exists(missing_file)
        assert result is False

    @pytest.mark.integration
    def test_directory_returns_true(self, tmp_path: Path) -> None:
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
    def test_creates_new_directory(self, tmp_path: Path) -> None:
        """新規ディレクトリを作成"""
        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()

        ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    @pytest.mark.integration
    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """ネストされたディレクトリを作成（parents=True）"""
        deep_dir = tmp_path / "a" / "b" / "c" / "d"
        assert not deep_dir.exists()

        ensure_directory(deep_dir)

        assert deep_dir.exists()
        assert (tmp_path / "a" / "b" / "c").exists()

    @pytest.mark.integration
    def test_existing_directory_no_error(self, tmp_path: Path) -> None:
        """既存ディレクトリ → エラーなし（exist_ok=True）"""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        # 2回目の呼び出しでエラーにならない
        ensure_directory(existing_dir)

        assert existing_dir.exists()

    @pytest.mark.integration
    def test_file_as_parent_raises_error(self, tmp_path: Path) -> None:
        """親パスがファイルの場合 → FileIOError"""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        # ファイルの下にディレクトリを作ろうとする
        invalid_dir = file_path / "subdir"

        with pytest.raises(FileIOError, match="Failed to create directory"):
            ensure_directory(invalid_dir)


# =============================================================================
# try_load_json テスト
# =============================================================================


class TestTryLoadJson:
    """try_load_json() 関数のテスト"""

    @pytest.mark.integration
    def test_missing_file_returns_default(self, tmp_path: Path) -> None:
        """存在しないファイル → デフォルト値"""
        missing_file = tmp_path / "missing.json"

        result = try_load_json(missing_file, default={"fallback": True})
        assert result == {"fallback": True}

    @pytest.mark.integration
    def test_missing_file_returns_none_when_no_default(self, tmp_path: Path) -> None:
        """存在しないファイル、デフォルトなし → None"""
        missing_file = tmp_path / "missing.json"

        result = try_load_json(missing_file)
        assert result is None

    @pytest.mark.integration
    def test_valid_json_returns_content(self, tmp_path: Path) -> None:
        """正常なJSON → 内容を返す"""
        valid_file = tmp_path / "valid.json"
        test_data = {"key": "value"}
        valid_file.write_text(json.dumps(test_data))

        result = try_load_json(valid_file)
        assert result == test_data

    @pytest.mark.integration
    def test_invalid_json_returns_default(self, tmp_path: Path) -> None:
        """不正なJSON → デフォルト値"""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json")

        result = try_load_json(invalid_file, default={"error": "fallback"})
        assert result == {"error": "fallback"}

    @pytest.mark.integration
    def test_invalid_json_returns_none_when_no_default(self, tmp_path: Path) -> None:
        """不正なJSON、デフォルトなし → None"""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{invalid json")

        result = try_load_json(invalid_file)
        assert result is None


# =============================================================================
# try_read_json_from_file テスト
# =============================================================================


class TestTryReadJsonFromFile:
    """try_read_json_from_file() 関数のテスト"""

    @pytest.mark.integration
    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        """存在しないファイル → None"""
        missing_file = tmp_path / "missing.txt"

        result = try_read_json_from_file(missing_file)
        assert result is None

    @pytest.mark.integration
    def test_valid_txt_json_returns_content(self, tmp_path: Path) -> None:
        """正常な.txt JSON → 内容を返す"""
        valid_file = tmp_path / "valid.txt"
        test_data = {"source_file": "L00001.txt", "keywords": ["a", "b"]}
        valid_file.write_text(json.dumps(test_data))

        result = try_read_json_from_file(valid_file)
        assert result == test_data

    @pytest.mark.integration
    def test_non_txt_extension_returns_none(self, tmp_path: Path) -> None:
        """非.txt拡張子 → None"""
        json_file = tmp_path / "data.json"
        json_file.write_text('{"key": "value"}')

        result = try_read_json_from_file(json_file)
        assert result is None

    @pytest.mark.integration
    def test_invalid_json_returns_none(self, tmp_path: Path) -> None:
        """不正なJSON → None"""
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("{invalid json content")

        result = try_read_json_from_file(invalid_file)
        assert result is None

    @pytest.mark.integration
    def test_empty_file_returns_none(self, tmp_path: Path) -> None:
        """空ファイル → None"""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        result = try_read_json_from_file(empty_file)
        assert result is None

    @pytest.mark.integration
    def test_utf8_content_handled(self, tmp_path: Path) -> None:
        """UTF-8コンテンツを正しく処理"""
        utf8_file = tmp_path / "utf8.txt"
        test_data = {"japanese": "日本語", "keywords": ["キーワード1", "キーワード2"]}
        utf8_file.write_text(
            json.dumps(test_data, ensure_ascii=False), encoding="utf-8"
        )

        result = try_read_json_from_file(utf8_file)
        assert result is not None
        assert result["japanese"] == "日本語"


# =============================================================================
# confirm_file_overwrite テスト
# =============================================================================


class TestConfirmFileOverwrite:
    """confirm_file_overwrite() 関数のテスト"""

    @pytest.mark.integration
    def test_missing_file_returns_true(self, tmp_path: Path) -> None:
        """存在しないファイル → True（上書き可）"""
        missing_file = tmp_path / "new_file.txt"

        result = confirm_file_overwrite(missing_file)
        assert result is True

    @pytest.mark.integration
    def test_existing_file_returns_false(self, tmp_path: Path) -> None:
        """存在するファイル、force=False → False"""
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("content")

        result = confirm_file_overwrite(existing_file)
        assert result is False

    @pytest.mark.integration
    def test_existing_file_with_force_returns_true(self, tmp_path: Path) -> None:
        """存在するファイル、force=True → True"""
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("content")

        result = confirm_file_overwrite(existing_file, force=True)
        assert result is True

    @pytest.mark.unit
    def test_force_false_by_default(self, tmp_path: Path) -> None:
        """force のデフォルト値は False"""
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("content")

        # デフォルト引数を使用
        result = confirm_file_overwrite(existing_file)
        assert result is False
