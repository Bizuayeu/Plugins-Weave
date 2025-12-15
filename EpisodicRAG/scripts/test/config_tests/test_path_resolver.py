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
    from application.grand import GrandDigestManager, ShadowGrandDigestManager
    from application.shadow import FileDetector, ShadowIO, ShadowTemplate
    from application.shadow.placeholder_manager import PlaceholderManager
    from application.tracking import DigestTimesTracker
    from domain.types.level import LevelHierarchyEntry


import pytest

from domain.exceptions import ConfigError
from infrastructure.config.path_resolver import PathResolver


class TestPathResolver:
    """PathResolverクラスのテスト"""

    @pytest.fixture
    def valid_config(self, tmp_path: Path):
        """有効な設定辞書（絶対パス必須）"""
        return {
            "base_dir": str(tmp_path),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
            },
        }

    @pytest.mark.unit
    def test_requires_absolute_base_dir(self) -> None:
        """PathResolver は base_dir が絶対パスであることを要求"""
        config = {
            "base_dir": "./relative/path",
            "paths": {"loops_dir": "data/Loops"},
        }

        with pytest.raises(ConfigError) as exc_info:
            PathResolver(config)

        assert "base_dir" in str(exc_info.value)
        assert "absolute" in str(exc_info.value).lower()

    @pytest.mark.unit
    def test_accepts_home_expansion(self) -> None:
        """PathResolver は ~ で始まるパスを受け入れる"""
        config = {
            "base_dir": "~",
            "paths": {"loops_dir": "data/Loops"},
        }

        resolver = PathResolver(config)

        assert resolver.base_dir.is_absolute()
        assert resolver.base_dir == Path.home().resolve()

    @pytest.mark.unit
    def test_no_plugin_root_parameter(self) -> None:
        """PathResolver は plugin_root パラメータを持たない"""
        import inspect

        sig = inspect.signature(PathResolver.__init__)
        params = list(sig.parameters.keys())

        # selfとconfigのみ
        assert "plugin_root" not in params
        assert params == ["self", "config"]

    @pytest.mark.unit
    def test_resolve_loop_dir(self, valid_config) -> None:
        """Loopディレクトリ解決"""
        resolver = PathResolver(valid_config)

        result = resolver.loops_path

        assert result.name == "Loops"
        assert "data" in str(result)

    @pytest.mark.unit
    def test_resolve_digest_dir(self, valid_config) -> None:
        """Digestディレクトリ解決"""
        resolver = PathResolver(valid_config)

        result = resolver.digests_path

        assert result.name == "Digests"

    @pytest.mark.unit
    def test_resolve_essences_dir(self, valid_config) -> None:
        """Essencesディレクトリ解決"""
        resolver = PathResolver(valid_config)

        result = resolver.essences_path

        assert result.name == "Essences"

    @pytest.mark.unit
    def test_missing_paths_section_raises_config_error(self, tmp_path: Path) -> None:
        """pathsセクション欠如時ConfigError"""
        config_without_paths = {"base_dir": str(tmp_path)}
        resolver = PathResolver(config_without_paths)

        with pytest.raises(ConfigError) as exc_info:
            resolver.resolve_path("loops_dir")

        assert "'paths' section missing" in str(exc_info.value)

    @pytest.mark.unit
    def test_missing_key_raises_config_error(self, valid_config) -> None:
        """存在しないキー指定時ConfigError"""
        resolver = PathResolver(valid_config)

        with pytest.raises(ConfigError) as exc_info:
            resolver.resolve_path("nonexistent_key")

        assert "Required configuration key missing" in str(exc_info.value)

    @pytest.mark.unit
    def test_relative_base_dir_raises_config_error(self) -> None:
        """相対パスのbase_dirはConfigError"""
        config = {"base_dir": "..", "paths": {"loops_dir": "data/Loops"}}

        with pytest.raises(ConfigError) as exc_info:
            PathResolver(config)

        assert "base_dir" in str(exc_info.value)

    @pytest.mark.unit
    def test_identity_file_path_configured(self, tmp_path: Path) -> None:
        """identity_file_pathが設定されている場合"""
        config = {
            "base_dir": str(tmp_path),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": "identity.md",
            },
        }
        resolver = PathResolver(config)

        result = resolver.get_identity_file_path()

        assert result is not None
        assert result.name == "identity.md"

    @pytest.mark.unit
    def test_identity_file_path_not_configured(self, valid_config) -> None:
        """identity_file_pathが未設定の場合None"""
        resolver = PathResolver(valid_config)

        result = resolver.get_identity_file_path()

        assert result is None

    @pytest.mark.unit
    def test_resolve_path_returns_absolute(self, valid_config) -> None:
        """resolve_pathは絶対パスを返す"""
        resolver = PathResolver(valid_config)

        result = resolver.resolve_path("loops_dir")

        assert result.is_absolute()


class TestTrustedExternalPaths:
    """trusted_external_paths機能のテスト"""

    @pytest.mark.unit
    def test_empty_trusted_paths_is_default(self, tmp_path: Path) -> None:
        """trusted_external_pathsが未設定時は空配列"""
        config = {"base_dir": str(tmp_path), "paths": {"loops_dir": "data/Loops"}}
        resolver = PathResolver(config)

        assert resolver._trusted_external_paths == []

    @pytest.mark.unit
    def test_base_dir_in_trusted_path_allowed(self, tmp_path: Path) -> None:
        """trusted_external_paths内のbase_dirは許可される"""
        external_dir = tmp_path / "external_data"
        external_dir.mkdir()

        config = {
            "base_dir": str(external_dir),
            "trusted_external_paths": [str(tmp_path)],
            "paths": {"loops_dir": "Loops"},
        }
        resolver = PathResolver(config)

        assert resolver.base_dir == external_dir.resolve()

    @pytest.mark.unit
    def test_base_dir_outside_trusted_paths_raises_error(self, tmp_path: Path) -> None:
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
            PathResolver(config)

        assert "trusted_external_paths" in str(exc_info.value)

    @pytest.mark.unit
    def test_tilde_expansion_in_trusted_paths(self) -> None:
        """trusted_external_pathsでチルダ展開が動作する"""
        home = Path.home()
        # base_dirはホームディレクトリ内（~/DEVの中）に設定
        config = {
            "base_dir": str(home / "DEV"),
            "trusted_external_paths": ["~/DEV"],
            "paths": {"loops_dir": "data/Loops"},
        }
        resolver = PathResolver(config)

        # チルダが展開されていることを確認
        assert all(not str(p).startswith("~") for p in resolver._trusted_external_paths)
        # 展開後はホームディレクトリベース
        assert resolver._trusted_external_paths[0] == (home / "DEV").resolve()

    @pytest.mark.unit
    def test_relative_path_in_trusted_paths_raises_error(self, tmp_path: Path) -> None:
        """trusted_external_pathsに相対パスを指定するとConfigError"""
        config = {
            "base_dir": str(tmp_path),
            "trusted_external_paths": ["../relative/path"],
            "paths": {"loops_dir": "data/Loops"},
        }

        with pytest.raises(ConfigError) as exc_info:
            PathResolver(config)

        assert "trusted_external_paths" in str(exc_info.value)
        assert "absolute path" in str(exc_info.value)

    @pytest.mark.unit
    def test_tilde_expansion_in_base_dir(self) -> None:
        """base_dirでチルダ展開が動作する"""
        home = Path.home()

        config = {
            "base_dir": "~",
            "trusted_external_paths": [str(home)],
            "paths": {"loops_dir": "data/Loops"},
        }
        resolver = PathResolver(config)

        assert resolver.base_dir == home.resolve()

    @pytest.mark.unit
    def test_absolute_path_in_base_dir_with_trusted_paths(self, tmp_path: Path) -> None:
        """絶対パスのbase_dirがtrusted_external_paths内なら許可"""
        external_dir = tmp_path / "data"
        external_dir.mkdir()

        config = {
            "base_dir": str(external_dir),
            "trusted_external_paths": [str(tmp_path)],
            "paths": {"loops_dir": "Loops"},
        }
        resolver = PathResolver(config)

        assert resolver.base_dir == external_dir.resolve()

    @pytest.mark.unit
    def test_multiple_trusted_paths(self, tmp_path: Path) -> None:
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
        resolver = PathResolver(config)

        assert resolver.base_dir == dir2.resolve()
        assert len(resolver._trusted_external_paths) == 2
