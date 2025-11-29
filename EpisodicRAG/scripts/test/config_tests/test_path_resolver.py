#!/usr/bin/env python3
"""
test_path_resolver.py
=====================

config/path_resolver.py のテスト
"""

import pytest

from config.path_resolver import PathResolver
from config.exceptions import ConfigError


class TestPathResolver:
    """PathResolverクラスのテスト"""

    @pytest.fixture
    def valid_config(self):
        """有効な設定辞書"""
        return {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
        }

    @pytest.mark.unit
    def test_resolve_loop_dir(self, temp_plugin_env, valid_config):
        """Loopディレクトリ解決"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.loops_path

        assert result.name == "Loops"
        assert "data" in str(result)

    @pytest.mark.unit
    def test_resolve_digest_dir(self, temp_plugin_env, valid_config):
        """Digestディレクトリ解決"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.digests_path

        assert result.name == "Digests"

    @pytest.mark.unit
    def test_resolve_essences_dir(self, temp_plugin_env, valid_config):
        """Essencesディレクトリ解決"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.essences_path

        assert result.name == "Essences"

    @pytest.mark.unit
    def test_missing_paths_section_raises_config_error(self, temp_plugin_env):
        """pathsセクション欠如時ConfigError"""
        config_without_paths = {"base_dir": "."}
        resolver = PathResolver(temp_plugin_env.plugin_root, config_without_paths)

        with pytest.raises(ConfigError) as exc_info:
            resolver.resolve_path("loops_dir")

        assert "'paths' section missing" in str(exc_info.value)

    @pytest.mark.unit
    def test_missing_key_raises_config_error(self, temp_plugin_env, valid_config):
        """存在しないキー指定時ConfigError"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        with pytest.raises(ConfigError) as exc_info:
            resolver.resolve_path("nonexistent_key")

        assert "Required configuration key missing" in str(exc_info.value)

    @pytest.mark.unit
    def test_base_dir_traversal_raises_config_error(self, temp_plugin_env):
        """base_dirがplugin_root外を指す場合ConfigError（セキュリティ対策）"""
        config = {"base_dir": "..", "paths": {"loops_dir": "data/Loops"}}

        with pytest.raises(ConfigError) as exc_info:
            PathResolver(temp_plugin_env.plugin_root, config)

        assert "Invalid configuration value for 'base_dir'" in str(exc_info.value)

    @pytest.mark.unit
    def test_base_dir_subdir_resolution(self, temp_plugin_env):
        """base_dirがサブディレクトリを指す場合は正常動作"""
        # サブディレクトリを作成
        subdir = temp_plugin_env.plugin_root / "subdir"
        subdir.mkdir()

        config = {"base_dir": "subdir", "paths": {"loops_dir": "data/Loops"}}
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        # base_dirがサブディレクトリを指す
        assert resolver.base_dir == subdir.resolve()

    @pytest.mark.unit
    def test_base_dir_with_dotdot_inside_plugin_root(self, temp_plugin_env):
        """サブディレクトリ内で..を使用してもplugin_root内なら正常動作"""
        # ネストしたサブディレクトリを作成
        nested = temp_plugin_env.plugin_root / "a" / "b"
        nested.mkdir(parents=True)

        # a/b/.. -> a に解決される（plugin_root内）
        config = {"base_dir": "a/b/..", "paths": {"loops_dir": "data/Loops"}}
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        # base_dirは a ディレクトリに解決される
        expected = (temp_plugin_env.plugin_root / "a").resolve()
        assert resolver.base_dir == expected

    @pytest.mark.unit
    def test_default_base_dir(self, temp_plugin_env):
        """base_dir未指定時のデフォルト"""
        config = {"paths": {"loops_dir": "data/Loops"}}
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        # デフォルトは "." なのでplugin_root自身
        assert resolver.base_dir == temp_plugin_env.plugin_root.resolve()

    @pytest.mark.unit
    def test_identity_file_path_configured(self, temp_plugin_env):
        """identity_file_pathが設定されている場合"""
        config = {
            "base_dir": ".",
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": "identity.md",
            },
        }
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        result = resolver.get_identity_file_path()

        assert result is not None
        assert result.name == "identity.md"

    @pytest.mark.unit
    def test_identity_file_path_not_configured(self, temp_plugin_env, valid_config):
        """identity_file_pathが未設定の場合None"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.get_identity_file_path()

        assert result is None

    @pytest.mark.unit
    def test_resolve_path_returns_absolute(self, temp_plugin_env, valid_config):
        """resolve_pathは絶対パスを返す"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.resolve_path("loops_dir")

        assert result.is_absolute()
