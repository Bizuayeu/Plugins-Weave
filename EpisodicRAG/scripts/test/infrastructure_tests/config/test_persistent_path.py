#!/usr/bin/env python3
"""
永続化パス解決ユーティリティのテスト
====================================

get_persistent_config_dir()のTDDテスト。
Claude Codeのプラグイン自動更新に影響されない永続化ディレクトリを提供。
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestGetPersistentConfigDir:
    """get_persistent_config_dir()のテスト"""

    @pytest.mark.unit
    def test_returns_path_under_claude_plugins(self) -> None:
        """~/.claude/plugins/.episodicrag パスを返す"""
        from infrastructure.config.persistent_path import get_persistent_config_dir

        result = get_persistent_config_dir()

        # パス構造を検証
        assert result.name == ".episodicrag"
        assert result.parent.name == "plugins"
        assert result.parent.parent.name == ".claude"

    @pytest.mark.unit
    def test_uses_home_directory(self) -> None:
        """ホームディレクトリを基準とする"""
        from infrastructure.config.persistent_path import get_persistent_config_dir

        result = get_persistent_config_dir()
        home = Path.home()

        # ホームディレクトリ配下であることを確認
        assert str(result).startswith(str(home))

    @pytest.mark.unit
    def test_creates_directory_if_not_exists(self) -> None:
        """ディレクトリがなければ作成する"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_home = Path(temp_dir)
            expected_dir = mock_home / ".claude" / "plugins" / ".episodicrag"

            # ディレクトリが存在しないことを確認
            assert not expected_dir.exists()

            with patch("infrastructure.config.persistent_path.Path.home", return_value=mock_home):
                from infrastructure.config.persistent_path import get_persistent_config_dir

                result = get_persistent_config_dir()

            # ディレクトリが作成されたことを確認
            assert expected_dir.exists()
            assert expected_dir.is_dir()
            assert result == expected_dir

    @pytest.mark.unit
    def test_returns_existing_directory(self) -> None:
        """既存ディレクトリがあればそのまま返す"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_home = Path(temp_dir)
            expected_dir = mock_home / ".claude" / "plugins" / ".episodicrag"

            # 事前にディレクトリを作成
            expected_dir.mkdir(parents=True, exist_ok=True)
            assert expected_dir.exists()

            with patch("infrastructure.config.persistent_path.Path.home", return_value=mock_home):
                from infrastructure.config.persistent_path import get_persistent_config_dir

                result = get_persistent_config_dir()

            # 同じディレクトリが返される
            assert result == expected_dir
            assert expected_dir.exists()

    @pytest.mark.unit
    def test_path_is_absolute(self) -> None:
        """絶対パスを返す"""
        from infrastructure.config.persistent_path import get_persistent_config_dir

        result = get_persistent_config_dir()

        assert result.is_absolute()


class TestPersistentConfigDirConstant:
    """PERSISTENT_CONFIG_DIR_NAME定数のテスト"""

    @pytest.mark.unit
    def test_constant_value(self) -> None:
        """定数値が正しい"""
        from domain.file_constants import PERSISTENT_CONFIG_DIR_NAME

        assert PERSISTENT_CONFIG_DIR_NAME == ".episodicrag"


class TestGetConfigPath:
    """get_config_path()のテスト"""

    @pytest.mark.unit
    def test_returns_config_json_in_persistent_dir(self) -> None:
        """永続化ディレクトリ内のconfig.jsonパスを返す"""
        from infrastructure.config.persistent_path import get_config_path

        config_path = get_config_path()

        assert config_path.name == "config.json"
        assert ".episodicrag" in str(config_path)

    @pytest.mark.unit
    def test_path_is_absolute(self) -> None:
        """絶対パスを返す"""
        from infrastructure.config.persistent_path import get_config_path

        config_path = get_config_path()

        assert config_path.is_absolute()

    @pytest.mark.unit
    def test_parent_is_persistent_config_dir(self) -> None:
        """親ディレクトリが永続化ディレクトリと一致"""
        from infrastructure.config.persistent_path import (
            get_config_path,
            get_persistent_config_dir,
        )

        config_path = get_config_path()
        persistent_dir = get_persistent_config_dir()

        assert config_path.parent == persistent_dir


class TestGetTemplateDir:
    """get_template_dir()のテスト"""

    @pytest.mark.unit
    def test_returns_claude_plugin_dir_or_none(self) -> None:
        """正常なディレクトリ名またはNoneを返す"""
        from infrastructure.config.persistent_path import get_template_dir

        template_dir = get_template_dir()

        # None または .claude-plugin ディレクトリ
        assert template_dir is None or template_dir.name == ".claude-plugin"

    @pytest.mark.unit
    def test_returns_absolute_path_when_found(self) -> None:
        """見つかった場合は絶対パスを返す"""
        from infrastructure.config.persistent_path import get_template_dir

        template_dir = get_template_dir()

        if template_dir is not None:
            assert template_dir.is_absolute()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
