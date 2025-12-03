#!/usr/bin/env python3
"""
test_path_resolver.py
=====================

config/path_resolver.py のテスト
"""

from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Dict, List, Tuple
    from test_helpers import TempPluginEnvironment
    from application.config import DigestConfig
    from application.tracking import DigestTimesTracker
    from application.shadow import ShadowTemplate, ShadowIO, FileDetector
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.grand import ShadowGrandDigestManager, GrandDigestManager
    from domain.types.level import LevelHierarchyEntry


import pytest

from domain.exceptions import ConfigError
from infrastructure.config.path_resolver import PathResolver


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
    def test_resolve_loop_dir(self, temp_plugin_env: "TempPluginEnvironment", valid_config) -> None:

        """Loopディレクトリ解決"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.loops_path

        assert result.name == "Loops"
        assert "data" in str(result)

    @pytest.mark.unit
    def test_resolve_digest_dir(self, temp_plugin_env: "TempPluginEnvironment", valid_config) -> None:

        """Digestディレクトリ解決"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.digests_path

        assert result.name == "Digests"

    @pytest.mark.unit
    def test_resolve_essences_dir(self, temp_plugin_env: "TempPluginEnvironment", valid_config) -> None:

        """Essencesディレクトリ解決"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.essences_path

        assert result.name == "Essences"

    @pytest.mark.unit
    def test_missing_paths_section_raises_config_error(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """pathsセクション欠如時ConfigError"""
        config_without_paths = {"base_dir": "."}
        resolver = PathResolver(temp_plugin_env.plugin_root, config_without_paths)

        with pytest.raises(ConfigError) as exc_info:
            resolver.resolve_path("loops_dir")

        assert "'paths' section missing" in str(exc_info.value)

    @pytest.mark.unit
    def test_missing_key_raises_config_error(self, temp_plugin_env: "TempPluginEnvironment", valid_config) -> None:

        """存在しないキー指定時ConfigError"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        with pytest.raises(ConfigError) as exc_info:
            resolver.resolve_path("nonexistent_key")

        assert "Required configuration key missing" in str(exc_info.value)

    @pytest.mark.unit
    def test_base_dir_traversal_raises_config_error(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """base_dirがplugin_root外を指す場合ConfigError（セキュリティ対策）"""
        config = {"base_dir": "..", "paths": {"loops_dir": "data/Loops"}}

        with pytest.raises(ConfigError) as exc_info:
            PathResolver(temp_plugin_env.plugin_root, config)

        assert "Invalid configuration value for 'base_dir'" in str(exc_info.value)

    @pytest.mark.unit
    def test_base_dir_subdir_resolution(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """base_dirがサブディレクトリを指す場合は正常動作"""
        # サブディレクトリを作成
        subdir = temp_plugin_env.plugin_root / "subdir"
        subdir.mkdir()

        config = {"base_dir": "subdir", "paths": {"loops_dir": "data/Loops"}}
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        # base_dirがサブディレクトリを指す
        assert resolver.base_dir == subdir.resolve()

    @pytest.mark.unit
    def test_base_dir_with_dotdot_inside_plugin_root(self, temp_plugin_env: "TempPluginEnvironment") -> None:

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
    def test_default_base_dir(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """base_dir未指定時のデフォルト"""
        config = {"paths": {"loops_dir": "data/Loops"}}
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        # デフォルトは "." なのでplugin_root自身
        assert resolver.base_dir == temp_plugin_env.plugin_root.resolve()

    @pytest.mark.unit
    def test_identity_file_path_configured(self, temp_plugin_env: "TempPluginEnvironment") -> None:

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
    def test_identity_file_path_not_configured(self, temp_plugin_env: "TempPluginEnvironment", valid_config) -> None:

        """identity_file_pathが未設定の場合None"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.get_identity_file_path()

        assert result is None

    @pytest.mark.unit
    def test_resolve_path_returns_absolute(self, temp_plugin_env: "TempPluginEnvironment", valid_config) -> None:

        """resolve_pathは絶対パスを返す"""
        resolver = PathResolver(temp_plugin_env.plugin_root, valid_config)

        result = resolver.resolve_path("loops_dir")

        assert result.is_absolute()


class TestTrustedExternalPaths:
    """trusted_external_paths機能のテスト"""

    @pytest.mark.unit
    def test_empty_trusted_paths_is_default(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """trusted_external_pathsが未設定時は空配列"""
        config = {"base_dir": ".", "paths": {"loops_dir": "data/Loops"}}
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        assert resolver._trusted_external_paths == []

    @pytest.mark.unit
    def test_base_dir_in_trusted_path_allowed(self, temp_plugin_env: "TempPluginEnvironment", tmp_path: Path) -> None:

        """trusted_external_paths内のbase_dirは許可される"""
        external_dir = tmp_path / "external_data"
        external_dir.mkdir()

        config = {
            "base_dir": str(external_dir),
            "trusted_external_paths": [str(tmp_path)],
            "paths": {"loops_dir": "Loops"},
        }
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        assert resolver.base_dir == external_dir.resolve()

    @pytest.mark.unit
    def test_base_dir_outside_trusted_paths_raises_error(self, temp_plugin_env: "TempPluginEnvironment", tmp_path: Path) -> None:

        """trusted_external_paths外のbase_dirはConfigError"""
        external_dir = tmp_path / "untrusted"
        external_dir.mkdir()
        other_dir = tmp_path / "other"
        other_dir.mkdir()

        config = {
            "base_dir": str(external_dir),
            "trusted_external_paths": [str(other_dir)],
            "paths": {"loops_dir": "Loops"},
        }

        with pytest.raises(ConfigError) as exc_info:
            PathResolver(temp_plugin_env.plugin_root, config)

        assert "trusted_external_paths" in str(exc_info.value)

    @pytest.mark.unit
    def test_tilde_expansion_in_trusted_paths(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """trusted_external_pathsでチルダ展開が動作する"""
        from pathlib import Path

        config = {
            "base_dir": ".",
            "trusted_external_paths": ["~/DEV"],
            "paths": {"loops_dir": "data/Loops"},
        }
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        # チルダが展開されていることを確認
        assert all(not str(p).startswith("~") for p in resolver._trusted_external_paths)
        # 展開後はホームディレクトリベース
        home = Path.home()
        assert resolver._trusted_external_paths[0] == (home / "DEV").resolve()

    @pytest.mark.unit
    def test_relative_path_in_trusted_paths_raises_error(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """trusted_external_pathsに相対パスを指定するとConfigError"""
        config = {
            "base_dir": ".",
            "trusted_external_paths": ["../relative/path"],
            "paths": {"loops_dir": "data/Loops"},
        }

        with pytest.raises(ConfigError) as exc_info:
            PathResolver(temp_plugin_env.plugin_root, config)

        assert "trusted_external_paths" in str(exc_info.value)
        assert "absolute path" in str(exc_info.value)

    @pytest.mark.unit
    def test_tilde_expansion_in_base_dir(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """base_dirでチルダ展開が動作する"""
        from pathlib import Path

        home = Path.home()

        config = {
            "base_dir": "~",
            "trusted_external_paths": [str(home)],
            "paths": {"loops_dir": "data/Loops"},
        }
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        assert resolver.base_dir == home.resolve()

    @pytest.mark.unit
    def test_backward_compatibility_without_trusted_paths(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """trusted_external_pathsなしの既存設定は動作する（後方互換性）"""
        config = {
            "base_dir": ".",
            "paths": {"loops_dir": "data/Loops"},
        }
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        assert resolver.base_dir == temp_plugin_env.plugin_root.resolve()

    @pytest.mark.unit
    def test_absolute_path_in_base_dir_with_trusted_paths(self, temp_plugin_env: "TempPluginEnvironment", tmp_path: Path) -> None:

        """絶対パスのbase_dirがtrusted_external_paths内なら許可"""
        external_dir = tmp_path / "data"
        external_dir.mkdir()

        config = {
            "base_dir": str(external_dir),
            "trusted_external_paths": [str(tmp_path)],
            "paths": {"loops_dir": "Loops"},
        }
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        assert resolver.base_dir == external_dir.resolve()

    @pytest.mark.unit
    def test_multiple_trusted_paths(self, temp_plugin_env: "TempPluginEnvironment", tmp_path: Path) -> None:

        """複数のtrusted_external_pathsが設定できる"""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        config = {
            "base_dir": str(dir2),
            "trusted_external_paths": [str(dir1), str(dir2)],
            "paths": {"loops_dir": "Loops"},
        }
        resolver = PathResolver(temp_plugin_env.plugin_root, config)

        assert resolver.base_dir == dir2.resolve()
        assert len(resolver._trusted_external_paths) == 2
