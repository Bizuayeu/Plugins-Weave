#!/usr/bin/env python3
"""
DigestPersistence Unit Tests
============================

Tests for application/finalize/persistence.py
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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

from domain.exceptions import DigestError, FileIOError, ValidationError

# =============================================================================
# DigestPersistence Initialization Tests
# =============================================================================


class TestDigestPersistenceInit:
    """DigestPersistence initialization tests"""

    def test_init_with_all_dependencies(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """Initializes with all required dependencies"""
        from application.finalize.persistence import DigestPersistence
        from application.grand import GrandDigestManager, ShadowGrandDigestManager
        from application.tracking import DigestTimesTracker
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        grand_manager = GrandDigestManager(config)
        shadow_manager = ShadowGrandDigestManager(config)
        times_tracker = DigestTimesTracker(config)

        persistence = DigestPersistence(
            config=config,
            grand_digest_manager=grand_manager,
            shadow_manager=shadow_manager,
            times_tracker=times_tracker,
        )

        assert persistence.config is config
        assert persistence.grand_digest_manager is grand_manager
        assert persistence.shadow_manager is shadow_manager
        assert persistence.times_tracker is times_tracker

    def test_init_with_custom_confirm_callback(self, temp_plugin_env: "TempPluginEnvironment") -> None:

        """Accepts custom confirm callback"""
        from application.finalize.persistence import DigestPersistence
        from application.grand import GrandDigestManager, ShadowGrandDigestManager
        from application.tracking import DigestTimesTracker
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        custom_callback = MagicMock(return_value=True)

        persistence = DigestPersistence(
            config=config,
            grand_digest_manager=GrandDigestManager(config),
            shadow_manager=ShadowGrandDigestManager(config),
            times_tracker=DigestTimesTracker(config),
            confirm_callback=custom_callback,
        )

        assert persistence.confirm_callback is custom_callback


# =============================================================================
# save_regular_digest Tests
# =============================================================================


class TestSaveRegularDigest:
    """save_regular_digest() tests"""

    @pytest.fixture
    def persistence(self, temp_plugin_env: "TempPluginEnvironment"):

        """Create DigestPersistence instance for testing"""
        from application.finalize.persistence import DigestPersistence
        from application.grand import GrandDigestManager, ShadowGrandDigestManager
        from application.tracking import DigestTimesTracker
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        return DigestPersistence(
            config=config,
            grand_digest_manager=GrandDigestManager(config),
            shadow_manager=ShadowGrandDigestManager(config),
            times_tracker=DigestTimesTracker(config),
            confirm_callback=lambda _: True,  # Always confirm
        )

    @pytest.fixture
    def sample_regular_digest(self):

        """Sample RegularDigest data"""
        return {
            "metadata": {
                "level": "weekly",
                "digest_name": "W0001",
                "created_at": "2025-01-01T00:00:00",
            },
            "overall_digest": {
                "name": "W0001",
                "timestamp": "2025-01-01T00:00:00",
                "source_files": ["Loop00001_test.txt"],
                "digest_type": "test",
                "keywords": ["test"],
                "abstract": "Test abstract",
                "impression": "Test impression",
            },
            "individual_digests": [],
        }

    def test_saves_to_correct_directory(self, persistence, sample_regular_digest, temp_plugin_env: "TempPluginEnvironment") -> None:

        """Saves digest to correct level directory"""
        result = persistence.save_regular_digest("weekly", sample_regular_digest, "W0001")

        assert result.exists()
        assert "1_Weekly" in str(result)
        assert result.name == "W0001.txt"

    def test_creates_directory_if_not_exists(
        self, persistence, sample_regular_digest, temp_plugin_env: "TempPluginEnvironment"
    ) -> None:

        """Creates target directory if it doesn't exist"""
        # Remove the directory first
        weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
        if weekly_dir.exists():
            import shutil

            shutil.rmtree(weekly_dir)

        result = persistence.save_regular_digest("weekly", sample_regular_digest, "W0001")

        assert result.exists()
        assert weekly_dir.exists()

    def test_saves_valid_json(self, persistence, sample_regular_digest) -> None:

        """Saves valid JSON content"""
        result = persistence.save_regular_digest("weekly", sample_regular_digest, "W0001")

        with open(result, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["metadata"]["level"] == "weekly"
        assert loaded["overall_digest"]["name"] == "W0001"

    def test_raises_validation_error_on_cancel(self, temp_plugin_env: "TempPluginEnvironment", sample_regular_digest) -> None:

        """Raises ValidationError when user cancels overwrite"""
        from application.finalize.persistence import DigestPersistence
        from application.grand import GrandDigestManager, ShadowGrandDigestManager
        from application.tracking import DigestTimesTracker
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        persistence = DigestPersistence(
            config=config,
            grand_digest_manager=GrandDigestManager(config),
            shadow_manager=ShadowGrandDigestManager(config),
            times_tracker=DigestTimesTracker(config),
            confirm_callback=lambda _: False,  # Cancel
        )

        # Create existing file
        persistence.save_regular_digest("weekly", sample_regular_digest, "W0001")

        # Try to overwrite - should raise
        with pytest.raises(ValidationError, match="User cancelled"):
            persistence.save_regular_digest("weekly", sample_regular_digest, "W0001")

    def test_overwrites_when_confirmed(self, persistence, sample_regular_digest) -> None:

        """Overwrites existing file when confirmed"""
        # First save
        persistence.save_regular_digest("weekly", sample_regular_digest, "W0001")

        # Modify and save again
        sample_regular_digest["overall_digest"]["abstract"] = "Modified"
        result = persistence.save_regular_digest("weekly", sample_regular_digest, "W0001")

        with open(result, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert loaded["overall_digest"]["abstract"] == "Modified"


# =============================================================================
# update_grand_digest Tests
# =============================================================================


class TestUpdateGrandDigest:
    """update_grand_digest() tests"""

    @pytest.fixture
    def persistence_with_mock_grand(self, temp_plugin_env: "TempPluginEnvironment"):

        """Create DigestPersistence with mocked GrandDigestManager"""
        from application.finalize.persistence import DigestPersistence
        from application.grand import ShadowGrandDigestManager
        from application.tracking import DigestTimesTracker
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        mock_grand = MagicMock()

        return DigestPersistence(
            config=config,
            grand_digest_manager=mock_grand,
            shadow_manager=ShadowGrandDigestManager(config),
            times_tracker=DigestTimesTracker(config),
        )

    def test_calls_grand_manager_update(self, persistence_with_mock_grand) -> None:

        """Calls GrandDigestManager.update_digest with correct arguments"""
        regular_digest = {
            "overall_digest": {
                "name": "W0001",
                "source_files": ["file1.txt"],
                "keywords": [],
                "abstract": "test",
                "impression": "test",
            }
        }

        persistence_with_mock_grand.update_grand_digest("weekly", regular_digest, "W0001")

        persistence_with_mock_grand.grand_digest_manager.update_digest.assert_called_once()
        call_args = persistence_with_mock_grand.grand_digest_manager.update_digest.call_args
        assert call_args[0][0] == "weekly"
        assert call_args[0][1] == "W0001"

    def test_raises_digest_error_for_invalid_overall_digest(self, persistence_with_mock_grand) -> None:

        """Raises DigestError when overall_digest is invalid"""
        regular_digest = {"overall_digest": None}

        with pytest.raises(DigestError):
            persistence_with_mock_grand.update_grand_digest("weekly", regular_digest, "W0001")

    def test_raises_digest_error_for_missing_overall_digest(self, persistence_with_mock_grand) -> None:

        """Raises DigestError when overall_digest is missing"""
        regular_digest = {}

        with pytest.raises(DigestError):
            persistence_with_mock_grand.update_grand_digest("weekly", regular_digest, "W0001")


# =============================================================================
# process_cascade_and_cleanup Tests
# =============================================================================


class TestProcessCascadeAndCleanup:
    """process_cascade_and_cleanup() tests"""

    @pytest.fixture
    def persistence_with_mocks(self, temp_plugin_env: "TempPluginEnvironment"):

        """Create DigestPersistence with mocked dependencies"""
        from application.finalize.persistence import DigestPersistence
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)

        mock_grand = MagicMock()
        mock_shadow = MagicMock()
        mock_times = MagicMock()

        persistence = DigestPersistence(
            config=config,
            grand_digest_manager=mock_grand,
            shadow_manager=mock_shadow,
            times_tracker=mock_times,
        )

        return persistence, mock_shadow, mock_times

    def test_calls_cascade_update(self, persistence_with_mocks) -> None:

        """Calls shadow_manager.cascade_update_on_digest_finalize"""
        persistence, mock_shadow, _ = persistence_with_mocks

        persistence.process_cascade_and_cleanup("weekly", ["file1.txt"], None)

        mock_shadow.cascade_update_on_digest_finalize.assert_called_once_with("weekly")

    def test_calls_times_tracker_save(self, persistence_with_mocks) -> None:

        """Calls times_tracker.save with correct arguments"""
        persistence, _, mock_times = persistence_with_mocks

        persistence.process_cascade_and_cleanup("weekly", ["file1.txt", "file2.txt"], None)

        mock_times.save.assert_called_once_with("weekly", ["file1.txt", "file2.txt"])

    def test_deletes_provisional_file(self, persistence_with_mocks, tmp_path: Path) -> None:

        """Deletes provisional file when provided"""
        persistence, _, _ = persistence_with_mocks

        # Create temporary file
        provisional_file = tmp_path / "W0001_Individual.txt"
        provisional_file.write_text("{}")

        persistence.process_cascade_and_cleanup("weekly", ["file1.txt"], provisional_file)

        assert not provisional_file.exists()

    def test_handles_missing_provisional_file(self, persistence_with_mocks, tmp_path: Path) -> None:

        """Handles non-existent provisional file gracefully"""
        persistence, _, _ = persistence_with_mocks

        missing_file = tmp_path / "missing.txt"

        # Should not raise
        persistence.process_cascade_and_cleanup("weekly", ["file1.txt"], missing_file)

    def test_handles_none_provisional_file(self, persistence_with_mocks) -> None:

        """Handles None provisional file gracefully"""
        persistence, _, _ = persistence_with_mocks

        # Should not raise
        persistence.process_cascade_and_cleanup("weekly", ["file1.txt"], None)


# =============================================================================
# _cleanup_provisional_file Tests
# =============================================================================


class TestCleanupProvisionalFile:
    """_cleanup_provisional_file() tests"""

    @pytest.fixture
    def persistence(self, temp_plugin_env: "TempPluginEnvironment"):

        """Create DigestPersistence instance"""
        from application.finalize.persistence import DigestPersistence
        from application.grand import GrandDigestManager, ShadowGrandDigestManager
        from application.tracking import DigestTimesTracker
        from application.config import DigestConfig

        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        return DigestPersistence(
            config=config,
            grand_digest_manager=GrandDigestManager(config),
            shadow_manager=ShadowGrandDigestManager(config),
            times_tracker=DigestTimesTracker(config),
        )

    def test_deletes_existing_file(self, persistence, tmp_path: Path) -> None:

        """Deletes existing file"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        persistence._cleanup_provisional_file(test_file)

        assert not test_file.exists()

    def test_handles_file_not_found(self, persistence, tmp_path: Path) -> None:

        """Handles FileNotFoundError gracefully"""
        missing_file = tmp_path / "missing.txt"

        # Should not raise
        persistence._cleanup_provisional_file(missing_file)

    def test_handles_permission_error(self, persistence, tmp_path: Path) -> None:

        """Handles PermissionError gracefully (logs warning)"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with patch("pathlib.Path.unlink", side_effect=PermissionError("Access denied")):
            # Should not raise, just log warning
            persistence._cleanup_provisional_file(test_file)

    def test_handles_none_input(self, persistence) -> None:

        """Handles None input gracefully"""
        # Should not raise
        persistence._cleanup_provisional_file(None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
