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
        assert builder._plugin_root is None
        assert builder._config_loader is None
        assert builder._path_resolver is None


class TestDigestConfigBuilderFluentInterface:
    """Fluent interface tests"""

    @pytest.mark.unit
    def test_with_plugin_root_returns_self(self) -> None:
        """with_plugin_root returns self for chaining"""
        builder = DigestConfigBuilder()
        result = builder.with_plugin_root(Path("/test"))
        assert result is builder

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
        builder = (
            DigestConfigBuilder().with_plugin_root(Path("/test")).with_custom_loader(mock_loader)
        )
        assert builder._plugin_root == Path("/test")
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
            "base_dir": ".",
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
        config_file = temp_plugin_env.config_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_build_with_plugin_root(self, config_env) -> None:
        """Build with explicit plugin root"""
        env = config_env["env"]
        config = DigestConfigBuilder().with_plugin_root(env.plugin_root).build()

        assert isinstance(config, DigestConfig)
        assert config.plugin_root == env.plugin_root
        assert config.config_file == config_env["config_file"]

    @pytest.mark.unit
    def test_build_produces_working_config(self, config_env) -> None:
        """Built config has all expected functionality"""
        env = config_env["env"]
        config = DigestConfigBuilder().with_plugin_root(env.plugin_root).build()

        # Verify core properties work
        assert config.loops_path is not None
        assert config.digests_path is not None
        assert config.essences_path is not None
        assert config.threshold is not None

    @pytest.mark.unit
    def test_build_with_custom_loader(self, config_env) -> None:
        """Build with custom ConfigLoader"""
        env = config_env["env"]

        # Create a mock loader
        mock_loader = MagicMock(spec=ConfigLoader)
        mock_loader.load.return_value = config_env["config_data"]

        config = (
            DigestConfigBuilder()
            .with_plugin_root(env.plugin_root)
            .with_custom_loader(mock_loader)
            .build()
        )

        assert isinstance(config, DigestConfig)
        mock_loader.load.assert_called_once()

    @pytest.mark.unit
    def test_build_raises_config_error_on_failure(self, config_env) -> None:
        """Build raises ConfigError on initialization failure"""
        env = config_env["env"]
        # Delete config file to cause failure
        config_env["config_file"].unlink()

        with pytest.raises(ConfigError):
            DigestConfigBuilder().with_plugin_root(env.plugin_root).build()


class TestDigestConfigBuilderBuildDefault:
    """DigestConfigBuilder.build_default() tests"""

    @pytest.fixture
    def config_env(self, temp_plugin_env: "TempPluginEnvironment"):
        """テスト用の設定環境を構築"""
        config_data = {
            "base_dir": ".",
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
        config_file = temp_plugin_env.config_dir / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        return {
            "env": temp_plugin_env,
            "config_data": config_data,
            "config_file": config_file,
        }

    @pytest.mark.unit
    def test_build_default_with_plugin_root(self, config_env) -> None:
        """build_default with explicit plugin root"""
        env = config_env["env"]
        config = DigestConfigBuilder.build_default(env.plugin_root)

        assert isinstance(config, DigestConfig)
        assert config.plugin_root == env.plugin_root

    @pytest.mark.unit
    def test_build_default_produces_same_result(self, config_env) -> None:
        """build_default produces same result as build()"""
        env = config_env["env"]

        config1 = DigestConfigBuilder().with_plugin_root(env.plugin_root).build()
        config2 = DigestConfigBuilder.build_default(env.plugin_root)

        # Both should have same plugin root
        assert config1.plugin_root == config2.plugin_root
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
            "base_dir": ".",
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
        config_file = temp_plugin_env.config_dir / "config.json"
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
        env = config_env["env"]

        # Direct instantiation
        direct_config = DigestConfig(plugin_root=env.plugin_root)

        # Builder instantiation
        builder_config = DigestConfigBuilder.build_default(env.plugin_root)

        # Should have same paths
        assert direct_config.plugin_root == builder_config.plugin_root
        assert direct_config.config_file == builder_config.config_file
        assert direct_config.loops_path == builder_config.loops_path
        assert direct_config.digests_path == builder_config.digests_path
        assert direct_config.essences_path == builder_config.essences_path
        assert direct_config.base_dir == builder_config.base_dir

    @pytest.mark.unit
    def test_builder_config_has_same_methods(self, config_env) -> None:
        """Builder config has all the same methods as direct config"""
        env = config_env["env"]
        config = DigestConfigBuilder.build_default(env.plugin_root)

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
