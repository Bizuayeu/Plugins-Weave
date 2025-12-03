#!/usr/bin/env python3
"""
ProvisionalLoader Unit Tests
============================

Tests for application/finalize/provisional_loader.py
"""

import json
import unittest
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

from domain.exceptions import DigestError

# =============================================================================
# ProvisionalLoader Initialization Tests
# =============================================================================


class TestProvisionalLoaderInit:
    """ProvisionalLoader initialization tests"""

    def test_init_with_dependencies(self, temp_plugin_env: "TempPluginEnvironment") -> None:
        """Initializes with required dependencies"""
        from application.config import DigestConfig
        from application.finalize.provisional_loader import ProvisionalLoader
        from application.grand import ShadowGrandDigestManager

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        shadow_manager = ShadowGrandDigestManager(config)

        loader = ProvisionalLoader(config=config, shadow_manager=shadow_manager)

        assert loader.config is config
        assert loader.shadow_manager is shadow_manager


# =============================================================================
# _get_source_path_for_level Tests
# =============================================================================


class TestGetSourcePathForLevel:
    """_get_source_path_for_level() tests"""

    @pytest.fixture
    def loader(self, temp_plugin_env: "TempPluginEnvironment"):
        """Create ProvisionalLoader instance"""
        from application.config import DigestConfig
        from application.finalize.provisional_loader import ProvisionalLoader
        from application.grand import ShadowGrandDigestManager

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        return ProvisionalLoader(config=config, shadow_manager=ShadowGrandDigestManager(config))

    def test_returns_loops_path_for_weekly(
        self, loader, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """Returns loops path for weekly level"""
        result = loader._get_source_path_for_level("weekly")
        assert result == temp_plugin_env.loops_path

    def test_returns_digest_dir_for_monthly(
        self, loader, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """Returns weekly digest dir for monthly level"""
        result = loader._get_source_path_for_level("monthly")
        assert "1_Weekly" in str(result)


# =============================================================================
# _get_provisional_path Tests
# =============================================================================


class TestGetProvisionalPath:
    """_get_provisional_path() tests"""

    @pytest.fixture
    def loader(self, temp_plugin_env: "TempPluginEnvironment"):
        """Create ProvisionalLoader instance"""
        from application.config import DigestConfig
        from application.finalize.provisional_loader import ProvisionalLoader
        from application.grand import ShadowGrandDigestManager

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        return ProvisionalLoader(config=config, shadow_manager=ShadowGrandDigestManager(config))

    def test_returns_correct_path_for_weekly(self, loader) -> None:
        """Returns correct provisional path for weekly"""
        result = loader._get_provisional_path("weekly", "0001")

        assert "Provisional" in str(result)
        assert result.name == "W0001_Individual.txt"

    def test_returns_correct_path_for_monthly(self, loader) -> None:
        """Returns correct provisional path for monthly"""
        result = loader._get_provisional_path("monthly", "0001")

        assert result.name == "M0001_Individual.txt"


# =============================================================================
# _load_provisional Tests
# =============================================================================


class TestLoadProvisional:
    """_load_provisional() tests"""

    @pytest.fixture
    def loader(self, temp_plugin_env: "TempPluginEnvironment"):
        """Create ProvisionalLoader instance"""
        from application.config import DigestConfig
        from application.finalize.provisional_loader import ProvisionalLoader
        from application.grand import ShadowGrandDigestManager

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        return ProvisionalLoader(config=config, shadow_manager=ShadowGrandDigestManager(config))

    def test_loads_valid_provisional_file(self, loader, tmp_path: Path) -> None:
        """Loads valid provisional file and returns digests"""
        provisional_data = {
            "individual_digests": [
                {"source_file": "file1.txt", "abstract": "test1"},
                {"source_file": "file2.txt", "abstract": "test2"},
            ]
        }
        provisional_file = tmp_path / "W0001_Individual.txt"
        provisional_file.write_text(json.dumps(provisional_data))

        digests, path = loader._load_provisional(provisional_file)

        assert len(digests) == 2
        assert digests[0]["source_file"] == "file1.txt"
        assert path == provisional_file

    def test_returns_empty_list_for_missing_digests(self, loader, tmp_path: Path) -> None:
        """Returns empty list when individual_digests key is missing"""
        provisional_data = {"other_key": "value"}
        provisional_file = tmp_path / "W0001_Individual.txt"
        provisional_file.write_text(json.dumps(provisional_data))

        digests, path = loader._load_provisional(provisional_file)

        assert digests == []
        assert path == provisional_file

    def test_raises_digest_error_for_invalid_format(self, loader, tmp_path: Path) -> None:
        """Raises DigestError for non-dict provisional data"""
        provisional_file = tmp_path / "W0001_Individual.txt"
        provisional_file.write_text(json.dumps(["not", "a", "dict"]))

        with pytest.raises(DigestError):
            loader._load_provisional(provisional_file)


# =============================================================================
# load_or_generate Tests
# =============================================================================


class TestLoadOrGenerate:
    """load_or_generate() tests"""

    @pytest.fixture
    def loader(self, temp_plugin_env: "TempPluginEnvironment"):
        """Create ProvisionalLoader instance"""
        from application.config import DigestConfig
        from application.finalize.provisional_loader import ProvisionalLoader
        from application.grand import ShadowGrandDigestManager

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        return ProvisionalLoader(config=config, shadow_manager=ShadowGrandDigestManager(config))

    def test_loads_existing_provisional(
        self, loader, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """Loads existing provisional file when present"""
        # Create provisional file
        provisional_dir = temp_plugin_env.digests_path / "1_Weekly" / "Provisional"
        provisional_dir.mkdir(parents=True, exist_ok=True)
        provisional_file = provisional_dir / "W0001_Individual.txt"
        provisional_data = {
            "individual_digests": [{"source_file": "file1.txt", "abstract": "test"}]
        }
        provisional_file.write_text(json.dumps(provisional_data))

        shadow_digest = {"source_files": ["file1.txt"]}
        digests, file_to_delete = loader.load_or_generate("weekly", shadow_digest, "0001")

        assert len(digests) == 1
        assert file_to_delete == provisional_file

    def test_generates_from_source_when_no_provisional(
        self, loader, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """Generates from source files when no provisional exists"""
        # Create source file
        loop_file = temp_plugin_env.loops_path / "Loop00001_test.txt"
        loop_data = {
            "overall_digest": {
                "digest_type": "test",
                "keywords": ["key1"],
                "abstract": "Test abstract",
                "impression": "Test impression",
            }
        }
        loop_file.write_text(json.dumps(loop_data))

        shadow_digest = {"source_files": ["Loop00001_test.txt"]}
        digests, file_to_delete = loader.load_or_generate("weekly", shadow_digest, "0001")

        assert len(digests) == 1
        assert digests[0]["source_file"] == "Loop00001_test.txt"
        assert file_to_delete is None


# =============================================================================
# _build_individual_entry Tests
# =============================================================================


class TestBuildIndividualEntry:
    """_build_individual_entry() tests"""

    @pytest.fixture
    def loader(self, temp_plugin_env: "TempPluginEnvironment"):
        """Create ProvisionalLoader instance"""
        from application.config import DigestConfig
        from application.finalize.provisional_loader import ProvisionalLoader
        from application.grand import ShadowGrandDigestManager

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        return ProvisionalLoader(config=config, shadow_manager=ShadowGrandDigestManager(config))

    def test_builds_entry_from_complete_data(self, loader) -> None:
        """Builds complete entry from source data"""
        source_data = {
            "overall_digest": {
                "digest_type": "conversation",
                "keywords": ["ai", "chat"],
                "abstract": "A conversation about AI",
                "impression": "Interesting discussion",
            }
        }

        entry = loader._build_individual_entry("Loop00001.txt", source_data)

        assert entry["source_file"] == "Loop00001.txt"
        assert entry["digest_type"] == "conversation"
        assert entry["keywords"] == ["ai", "chat"]
        assert entry["abstract"] == "A conversation about AI"
        assert entry["impression"] == "Interesting discussion"

    def test_builds_entry_with_missing_fields(self, loader) -> None:
        """Builds entry with defaults for missing fields"""
        source_data = {"overall_digest": {}}

        entry = loader._build_individual_entry("Loop00001.txt", source_data)

        assert entry["source_file"] == "Loop00001.txt"
        assert entry["digest_type"] == ""
        assert entry["keywords"] == []
        assert entry["abstract"] == ""
        assert entry["impression"] == ""

    def test_builds_entry_with_no_overall_digest(self, loader) -> None:
        """Builds entry when overall_digest is missing"""
        source_data = {}

        entry = loader._build_individual_entry("Loop00001.txt", source_data)

        assert entry["source_file"] == "Loop00001.txt"
        assert entry["digest_type"] == ""


# =============================================================================
# generate_from_source Tests
# =============================================================================


class TestGenerateFromSource:
    """generate_from_source() tests"""

    @pytest.fixture
    def loader(self, temp_plugin_env: "TempPluginEnvironment"):
        """Create ProvisionalLoader instance"""
        from application.config import DigestConfig
        from application.finalize.provisional_loader import ProvisionalLoader
        from application.grand import ShadowGrandDigestManager

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        return ProvisionalLoader(config=config, shadow_manager=ShadowGrandDigestManager(config))

    def test_generates_from_multiple_sources(
        self, loader, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """Generates digests from multiple source files"""
        # Create source files
        for i in range(1, 4):
            loop_file = temp_plugin_env.loops_path / f"Loop0000{i}_test.txt"
            loop_data = {
                "overall_digest": {
                    "digest_type": f"type{i}",
                    "keywords": [f"key{i}"],
                    "abstract": f"Abstract {i}",
                    "impression": f"Impression {i}",
                }
            }
            loop_file.write_text(json.dumps(loop_data))

        shadow_digest = {
            "source_files": ["Loop00001_test.txt", "Loop00002_test.txt", "Loop00003_test.txt"]
        }

        digests = loader.generate_from_source("weekly", shadow_digest)

        assert len(digests) == 3
        assert digests[0]["digest_type"] == "type1"
        assert digests[2]["digest_type"] == "type3"

    def test_skips_missing_files(self, loader, temp_plugin_env: "TempPluginEnvironment") -> None:
        """Skips missing source files and continues"""
        # Create only one file
        loop_file = temp_plugin_env.loops_path / "Loop00001_test.txt"
        loop_data = {"overall_digest": {"abstract": "test"}}
        loop_file.write_text(json.dumps(loop_data))

        shadow_digest = {"source_files": ["Loop00001_test.txt", "missing.txt"]}

        digests = loader.generate_from_source("weekly", shadow_digest)

        assert len(digests) == 1
        assert digests[0]["source_file"] == "Loop00001_test.txt"

    def test_skips_invalid_json_files(
        self, loader, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:
        """Skips files with invalid JSON"""
        # Create valid file
        valid_file = temp_plugin_env.loops_path / "Loop00001_test.txt"
        valid_file.write_text(json.dumps({"overall_digest": {"abstract": "test"}}))

        # Create invalid file
        invalid_file = temp_plugin_env.loops_path / "Loop00002_test.txt"
        invalid_file.write_text("not valid json {{{")

        shadow_digest = {"source_files": ["Loop00001_test.txt", "Loop00002_test.txt"]}

        digests = loader.generate_from_source("weekly", shadow_digest)

        assert len(digests) == 1

    def test_returns_empty_list_for_no_source_files(self, loader) -> None:
        """Returns empty list when no source files"""
        shadow_digest = {"source_files": []}

        digests = loader.generate_from_source("weekly", shadow_digest)

        assert digests == []

    def test_handles_missing_source_files_key(self, loader) -> None:
        """Handles missing source_files key"""
        shadow_digest = {}

        digests = loader.generate_from_source("weekly", shadow_digest)

        assert digests == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
