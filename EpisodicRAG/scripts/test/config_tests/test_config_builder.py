#!/usr/bin/env python3
"""
DigestConfigBuilder テスト
==========================

Builder Pattern 実装のテスト。
- Fluent interface
- 依存性注入
- デフォルト構築
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

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

from application.config import DigestConfig, DigestConfigBuilder
from domain.exceptions import ConfigError
from infrastructure.config import ConfigLoader

# =============================================================================
# DigestConfigBuilder Basic Tests
# =============================================================================


class TestDigestConfigBuilderInit:
    """DigestConfigBuilder initialization tests"""

    @pytest.mark.unit
    def test_init_creates_empty_builder(self) -> None:
        """Initializes with no configuration"""
        builder = DigestConfigBuilder()
        # Internal state should be None
        assert builder._config_loader is None
        assert builder._path_resolver is None

    @pytest.mark.unit
    def test_no_plugin_root_attribute(self) -> None:
        """DigestConfigBuilder does not have _plugin_root attribute"""
        builder = DigestConfigBuilder()
        assert not hasattr(builder, "_plugin_root")


class TestDigestConfigBuilderFluentInterface:
    """Fluent interface tests"""

    @pytest.mark.unit
    def test_with_custom_loader_returns_self(self) -> None:
        """with_custom_loader returns self for chaining"""
        builder = DigestConfigBuilder()
        mock_loader = MagicMock(spec=ConfigLoader)
        result = builder.with_custom_loader(mock_loader)
        assert result is builder

    @pytest.mark.unit
    def test_method_chaining(self) -> None:
        """Methods can be chained"""
        mock_loader = MagicMock(spec=ConfigLoader)
        builder = DigestConfigBuilder().with_custom_loader(mock_loader)
        assert builder._config_loader is mock_loader


# =============================================================================
# DigestConfigBuilder Build Tests
# =============================================================================


class TestDigestConfigBuilderBuild:
    """DigestConfigBuilder.build() tests"""

    @pytest.fixture
    def config_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """テスト用の設定環境を構築"""
        config_data = {
            "base_dir": str(temp_plugin_env.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
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
        # 永続化ディレクトリにconfig.jsonを配置
        config_file = temp_plugin_env.persistent_config_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_build_returns_digest_config(self, config_env) -> None:
        """Build returns DigestConfig instance"""
        config = DigestConfigBuilder().build()

        assert isinstance(config, DigestConfig)
        assert config.config_file == config_env["config_file"]

    @pytest.mark.unit
    def test_build_produces_working_config(self, config_env) -> None:
        """Built config has all expected functionality"""
        config = DigestConfigBuilder().build()

        # Verify core properties work
        assert config.loops_path is not None
        assert config.digests_path is not None
        assert config.essences_path is not None
        assert config.threshold is not None

    @pytest.mark.unit
    def test_build_with_custom_loader(self, config_env) -> None:
        """Build with custom ConfigLoader"""
        # Create a mock loader
        mock_loader = MagicMock(spec=ConfigLoader)
        mock_loader.load.return_value = config_env["config_data"]

        config = DigestConfigBuilder().with_custom_loader(mock_loader).build()

        assert isinstance(config, DigestConfig)
        mock_loader.load.assert_called_once()

    @pytest.mark.unit
    def test_build_raises_config_error_on_failure(self, config_env) -> None:
        """Build raises ConfigError on initialization failure"""
        # Delete config file to cause failure
        config_env["config_file"].unlink()

        with pytest.raises(ConfigError):
            DigestConfigBuilder().build()


class TestDigestConfigBuilderBuildDefault:
    """DigestConfigBuilder.build_default() tests"""

    @pytest.fixture
    def config_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """テスト用の設定環境を構築"""
        config_data = {
            "base_dir": str(temp_plugin_env.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
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
        # 永続化ディレクトリにconfig.jsonを配置
        config_file = temp_plugin_env.persistent_config_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_build_default_returns_digest_config(self, config_env) -> None:
        """build_default returns DigestConfig instance"""
        config = DigestConfigBuilder.build_default()

        assert isinstance(config, DigestConfig)

    @pytest.mark.unit
    def test_build_default_produces_same_result(self, config_env) -> None:
        """build_default produces same result as build()"""
        config1 = DigestConfigBuilder().build()
        config2 = DigestConfigBuilder.build_default()

        # Both should have same paths
        assert config1.loops_path == config2.loops_path
        assert config1.digests_path == config2.digests_path


# =============================================================================
# DigestConfigBuilder Equivalence Tests
# =============================================================================


class TestDigestConfigBuilderEquivalence:
    """Test that Builder produces equivalent results to direct instantiation"""

    @pytest.fixture
    def config_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """テスト用の設定環境を構築"""
        config_data = {
            "base_dir": str(temp_plugin_env.plugin_root),
            "paths": {
                "loops_dir": "data/Loops",
                "digests_dir": "data/Digests",
                "essences_dir": "data/Essences",
                "identity_file_path": None,
            },
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
        # 永続化ディレクトリにconfig.jsonを配置
        config_file = temp_plugin_env.persistent_config_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_builder_produces_equivalent_config(self, config_env) -> None:
        """Builder produces config equivalent to direct instantiation"""
        # Direct instantiation
        direct_config = DigestConfig()

        # Builder instantiation
        builder_config = DigestConfigBuilder.build_default()

        # Should have same paths
        assert direct_config.config_file == builder_config.config_file
        assert direct_config.loops_path == builder_config.loops_path
        assert direct_config.digests_path == builder_config.digests_path
        assert direct_config.essences_path == builder_config.essences_path
        assert direct_config.base_dir == builder_config.base_dir

    @pytest.mark.unit
    def test_builder_config_has_same_methods(self, config_env) -> None:
        """Builder config has all the same methods as direct config"""
        config = DigestConfigBuilder.build_default()

        # Verify key methods exist and work
        assert hasattr(config, "get_level_dir")
        assert hasattr(config, "get_provisional_dir")
        assert hasattr(config, "get_source_dir")
        assert hasattr(config, "get_threshold")
        assert hasattr(config, "validate_directory_structure")

        # Verify they work
        config.get_level_dir("weekly")
        config.get_provisional_dir("weekly")
        config.get_threshold("weekly")


# =============================================================================
# Import Tests
# =============================================================================


class TestDigestConfigBuilderPathResolver:
    """カスタムPathResolver注入のテスト"""

    @pytest.mark.unit
    def test_with_custom_path_resolver_stores_resolver(self) -> None:
        """with_custom_path_resolver()がresolverを保存"""
        from infrastructure.config import PathResolver

        mock_resolver = MagicMock(spec=PathResolver)
        builder = DigestConfigBuilder().with_custom_path_resolver(mock_resolver)
        assert builder._path_resolver is mock_resolver

    @pytest.mark.unit
    def test_with_custom_path_resolver_returns_self(self) -> None:
        """fluent interfaceでselfを返す"""
        from infrastructure.config import PathResolver

        mock_resolver = MagicMock(spec=PathResolver)
        builder = DigestConfigBuilder()
        result = builder.with_custom_path_resolver(mock_resolver)
        assert result is builder

    @pytest.mark.unit
    def test_method_chaining_with_path_resolver(self) -> None:
        """PathResolverを含むメソッドチェーン"""
        from infrastructure.config import PathResolver

        mock_loader = MagicMock(spec=ConfigLoader)
        mock_resolver = MagicMock(spec=PathResolver)
        builder = (
            DigestConfigBuilder()
            .with_custom_loader(mock_loader)
            .with_custom_path_resolver(mock_resolver)
        )
        assert builder._config_loader is mock_loader
        assert builder._path_resolver is mock_resolver


# =============================================================================
# Import Tests
# =============================================================================


class TestDigestConfigBuilderImports:
    """DigestConfigBuilder import path tests"""

    @pytest.mark.unit
    def test_import_from_package(self) -> None:
        """Import from application.config package"""
        from application.config import DigestConfigBuilder

        assert DigestConfigBuilder is not None

    @pytest.mark.unit
    def test_import_from_module(self) -> None:
        """Import from application.config.config_builder module"""
        from application.config.config_builder import DigestConfigBuilder

        assert DigestConfigBuilder is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
