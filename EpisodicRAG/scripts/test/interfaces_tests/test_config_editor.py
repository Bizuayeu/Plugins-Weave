#!/usr/bin/env python3
"""
ConfigEditor クラスのテスト
===========================

ConfigEditor クラスの基本機能とエラーハンドリングのテスト。
test_digest_config.py から分割。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pytest

from domain.exceptions import FileIOError


class TestConfigEditor(unittest.TestCase):
    """ConfigEditor クラスのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self) -> None:

        """設定ファイルを作成"""
        config_data = {
            "_comment_base_dir": "Data base directory",
            "base_dir": ".",
            "_comment_trusted_external_paths": "Trusted paths",
            "trusted_external_paths": [],
            "_comment_paths": "Paths config",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
            "_comment_levels": "Threshold config",
            "levels": {
                "weekly_threshold": 5,
                "monthly_threshold": 5,
                "quarterly_threshold": 3,
                "annual_threshold": 4,
                "triennial_threshold": 3,
                "decadal_threshold": 3,
                "multi_decadal_threshold": 3,
                "centurial_threshold": 4,
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_show_returns_current_config(self) -> None:

        """show が現在の設定を返す"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.show()

        assert result["status"] == "ok"
        assert "config" in result
        assert "resolved_paths" in result
        assert result["config"]["base_dir"] == "."

    @pytest.mark.unit
    def test_show_excludes_comment_fields(self) -> None:

        """show がコメントフィールドを除外する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.show()

        config = result["config"]
        for key in config.keys():
            assert not key.startswith("_comment")

    @pytest.mark.unit
    def test_show_includes_resolved_paths(self) -> None:

        """show が解決済みパスを含む"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.show()

        resolved = result["resolved_paths"]
        assert "plugin_root" in resolved
        assert "loops_path" in resolved
        assert "digests_path" in resolved
        assert "essences_path" in resolved

    @pytest.mark.unit
    def test_set_value_updates_nested_key(self) -> None:

        """set_value がネストされたキーを更新する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.set_value("levels.weekly_threshold", 7)

        assert result["status"] == "ok"
        assert result["old_value"] == 5
        assert result["new_value"] == 7

        # ファイルが更新されていることを確認
        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        assert saved_config["levels"]["weekly_threshold"] == 7

    @pytest.mark.unit
    def test_set_value_converts_threshold_to_int(self) -> None:

        """set_value が閾値を整数に変換する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.set_value("levels.weekly_threshold", "10")

        assert result["status"] == "ok"
        assert result["new_value"] == 10
        assert isinstance(result["new_value"], int)

    @pytest.mark.unit
    def test_update_replaces_config(self) -> None:

        """update が設定を更新する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        new_config = {"base_dir": "../other"}
        result = editor.update(new_config)

        assert result["status"] == "ok"
        assert "base_dir" in result["updated_keys"]

    @pytest.mark.unit
    def test_update_preserves_comments(self) -> None:

        """update がコメントを保持する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        new_config = {"base_dir": "../other"}
        editor.update(new_config)

        with open(self.plugin_root / ".claude-plugin" / "config.json", "r", encoding="utf-8") as f:
            saved_config = json.load(f)

        assert "_comment_base_dir" in saved_config

    @pytest.mark.unit
    def test_add_trusted_path_adds_new_path(self) -> None:

        """add_trusted_path が新しいパスを追加する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.add_trusted_path("~/DEV/production")

        assert result["status"] == "ok"
        assert "~/DEV/production" in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_add_trusted_path_rejects_relative_paths(self) -> None:

        """add_trusted_path が相対パスを拒否する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.add_trusted_path("relative/path")

        assert result["status"] == "error"
        assert "absolute" in result["error"].lower()

    @pytest.mark.unit
    def test_add_trusted_path_handles_duplicates(self) -> None:

        """add_trusted_path が重複を処理する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        editor.add_trusted_path("~/DEV/production")
        result = editor.add_trusted_path("~/DEV/production")

        assert result["status"] == "ok"
        assert "already exists" in result["message"].lower()

    @pytest.mark.unit
    def test_remove_trusted_path_removes_existing(self) -> None:

        """remove_trusted_path が既存のパスを削除する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        editor.add_trusted_path("~/DEV/production")
        result = editor.remove_trusted_path("~/DEV/production")

        assert result["status"] == "ok"
        assert "~/DEV/production" not in result["trusted_external_paths"]

    @pytest.mark.unit
    def test_remove_trusted_path_handles_nonexistent(self) -> None:

        """remove_trusted_path が存在しないパスを処理する"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.remove_trusted_path("~/nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    @pytest.mark.unit
    def test_list_trusted_paths_returns_all_paths(self) -> None:

        """list_trusted_paths が全パスを返す"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        editor.add_trusted_path("~/path1")
        editor.add_trusted_path("~/path2")
        result = editor.list_trusted_paths()

        assert result["status"] == "ok"
        assert result["count"] == 2
        assert "~/path1" in result["trusted_external_paths"]


class TestConfigEditorErrors(unittest.TestCase):
    """ConfigEditor エラーハンドリングのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_show_raises_when_config_missing(self) -> None:

        """設定ファイルがない場合に FileIOError"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)

        with pytest.raises(FileIOError):
            editor.show()


class TestConfigEditorResolvePath(unittest.TestCase):
    """ConfigEditor _resolve_path メソッドのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        self._create_config()

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_config(self) -> None:

        """設定ファイルを作成"""
        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    @pytest.mark.unit
    def test_resolve_absolute_path(self) -> None:

        """絶対パスはそのまま解決される"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        # Windowsでも動作するよう、tempディレクトリを使用
        abs_path = str(self.plugin_root / "some" / "path")
        result = editor._resolve_path(abs_path)

        assert result.is_absolute()

    @pytest.mark.unit
    def test_resolve_relative_path(self) -> None:

        """相対パスはbase_dirを基準に解決される"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor._resolve_path("subdir/file.txt")

        assert result.is_absolute()
        # plugin_root配下に解決されることを確認
        assert str(self.plugin_root) in str(result)


class TestConfigEditorSetValueErrors(unittest.TestCase):
    """ConfigEditor set_value エラーハンドリングのテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)
        config_data = {
            "base_dir": ".",
            "levels": {"weekly_threshold": 5},
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_set_invalid_threshold_returns_error(self) -> None:

        """無効な閾値（整数に変換できない値）でエラーを返す"""
        from interfaces.digest_config import ConfigEditor

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.set_value("levels.weekly_threshold", "not_a_number")

        assert result["status"] == "error"
        assert "integer" in result["error"].lower()


class TestConfigEditorIdentityPath(unittest.TestCase):
    """ConfigEditor identity_file_path 処理のテスト"""

    def setUp(self) -> None:

        """テスト環境をセットアップ"""
        self.temp_dir = tempfile.mkdtemp()
        self.plugin_root = Path(self.temp_dir)
        (self.plugin_root / ".claude-plugin").mkdir(parents=True)

    def tearDown(self) -> None:

        """一時ディレクトリを削除"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_show_with_identity_file_path(self) -> None:

        """identity_file_pathがある場合に解決済みパスに含まれる"""
        from interfaces.digest_config import ConfigEditor

        config_data = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": "identity.json",
            },
        }
        with open(self.plugin_root / ".claude-plugin" / "config.json", "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        editor = ConfigEditor(plugin_root=self.plugin_root)
        result = editor.show()

        assert "identity_file_path" in result["resolved_paths"]


if __name__ == "__main__":
    unittest.main()
