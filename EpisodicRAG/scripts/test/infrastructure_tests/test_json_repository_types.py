#!/usr/bin/env python3
"""
JSON Repository Type Safety Tests
=================================

json_repositoryモジュールの型安全性を確認するテスト。

TDD Red Phase: ジェネリック型オーバーロードのテスト。
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from test.test_helpers import TempPluginEnvironment


@pytest.mark.unit
class TestJsonRepositoryTypeSafety:
    """JSON操作の型安全性テスト"""

    def test_load_json_returns_dict(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """load_jsonがDict型を返すことを確認"""
        from infrastructure.json_repository import load_json

        # テスト用JSONファイルを作成
        test_file = temp_plugin_env.plugin_root / "test.json"
        test_file.write_text('{"key": "value", "count": 42}', encoding="utf-8")

        result = load_json(test_file)

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["count"] == 42

    def test_save_json_accepts_dict(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """save_jsonがDict型を受け入れることを確認"""
        from infrastructure.json_repository import save_json, load_json

        test_file = temp_plugin_env.plugin_root / "output.json"
        data = {"status": "success", "items": [1, 2, 3]}

        save_json(test_file, data)

        # 保存したファイルを読み込んで検証
        loaded = load_json(test_file)
        assert loaded == data

    def test_try_load_json_returns_default_on_missing(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """try_load_jsonがファイル不在時にデフォルト値を返すことを確認"""
        from infrastructure.json_repository import try_load_json

        missing_file = temp_plugin_env.plugin_root / "nonexistent.json"
        default_value = {"default": True}

        result = try_load_json(missing_file, default=default_value)

        assert result == default_value

    def test_try_load_json_returns_none_when_no_default(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """try_load_jsonがデフォルト未指定時にNoneを返すことを確認"""
        from infrastructure.json_repository import try_load_json

        missing_file = temp_plugin_env.plugin_root / "nonexistent.json"

        result = try_load_json(missing_file)

        assert result is None

    def test_safe_read_json_with_valid_file(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """safe_read_jsonが有効なファイルを読み込めることを確認"""
        from infrastructure.json_repository import safe_read_json

        test_file = temp_plugin_env.plugin_root / "valid.json"
        test_file.write_text('{"valid": true}', encoding="utf-8")

        result = safe_read_json(test_file)

        assert result is not None
        assert result["valid"] is True

    def test_safe_read_json_returns_none_on_invalid_json(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """safe_read_jsonが無効なJSONでNoneを返すことを確認（raise_on_error=False）"""
        from infrastructure.json_repository import safe_read_json

        test_file = temp_plugin_env.plugin_root / "invalid.json"
        test_file.write_text('{"invalid": }', encoding="utf-8")

        result = safe_read_json(test_file, raise_on_error=False)

        assert result is None


@pytest.mark.unit
class TestJsonRepositoryErrorHandling:
    """JSON操作のエラーハンドリングテスト"""

    def test_load_json_raises_on_missing_file(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """load_jsonがファイル不在時にFileIOErrorを発生させることを確認"""
        from infrastructure.json_repository import load_json
        from domain.exceptions import FileIOError

        missing_file = temp_plugin_env.plugin_root / "missing.json"

        with pytest.raises(FileIOError):
            load_json(missing_file)

    def test_load_json_raises_on_invalid_json(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """load_jsonが無効なJSONでFileIOErrorを発生させることを確認"""
        from infrastructure.json_repository import load_json
        from domain.exceptions import FileIOError

        test_file = temp_plugin_env.plugin_root / "invalid.json"
        test_file.write_text('{"broken": }', encoding="utf-8")

        with pytest.raises(FileIOError):
            load_json(test_file)

    def test_safe_read_json_raises_on_invalid_when_enabled(
        self, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """safe_read_jsonがraise_on_error=Trueで例外を発生させることを確認"""
        from infrastructure.json_repository import safe_read_json
        from domain.exceptions import FileIOError

        test_file = temp_plugin_env.plugin_root / "invalid.json"
        test_file.write_text('not valid json', encoding="utf-8")

        with pytest.raises(FileIOError):
            safe_read_json(test_file, raise_on_error=True)
