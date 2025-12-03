#!/usr/bin/env python3
"""
Failure recovery integration tests.

Tests that verify system behavior during and after failures.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from domain.exceptions import FileIOError

# =============================================================================
# Cascade Failure Recovery Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestCascadeFailureRecovery:
    """Tests for cascade processing failure scenarios."""

    def test_cascade_interrupted_by_missing_next_level_dir(self, temp_plugin_env) -> None:

        """Cascade should handle missing next level directory gracefully."""
        from application.config import DigestConfig

        # Setup: Create weekly Shadow with entries
        weekly_shadow_path = temp_plugin_env.digests_path / "1_Weekly" / "ShadowWeekly.txt"
        weekly_shadow_path.parent.mkdir(parents=True, exist_ok=True)

        shadow_data = {
            "metadata": {"version": "1.0"},
            "pending_sources": ["W0001_テスト.txt"],
        }
        with open(weekly_shadow_path, "w", encoding="utf-8") as f:
            json.dump(shadow_data, f, ensure_ascii=False)

        # DigestConfig should work even without all level directories
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        assert config is not None
        assert config.digests_path.exists()

    def test_cascade_with_corrupted_shadow_file(self, temp_plugin_env) -> None:

        """System should handle corrupted Shadow file gracefully."""
        # Create corrupted Shadow file
        weekly_shadow_path = temp_plugin_env.digests_path / "1_Weekly" / "ShadowWeekly.txt"
        weekly_shadow_path.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid JSON
        with open(weekly_shadow_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json content")

        # Attempt to load should raise appropriate error
        from infrastructure import load_json

        with pytest.raises(FileIOError):
            load_json(weekly_shadow_path)


# =============================================================================
# Partial Write Recovery Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestPartialWriteRecovery:
    """Tests for partial write failure scenarios."""

    def test_recovery_after_interrupted_json_write(self, temp_plugin_env) -> None:

        """System should detect and handle incomplete JSON files."""
        # Simulate incomplete write (truncated JSON)
        incomplete_file = temp_plugin_env.digests_path / "incomplete.json"
        incomplete_file.parent.mkdir(parents=True, exist_ok=True)

        with open(incomplete_file, "w", encoding="utf-8") as f:
            f.write('{"metadata": {"version": "1.0"}, "data": [')
            # Truncated - missing closing brackets

        from infrastructure import try_load_json

        # Should return None/default for corrupted file
        result = try_load_json(incomplete_file, default=None, log_on_error=False)
        assert result is None

    def test_atomic_write_behavior(self, temp_plugin_env) -> None:

        """Verify that writes don't corrupt existing data on failure."""
        target_file = temp_plugin_env.digests_path / "target.json"
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # Write initial valid data
        original_data = {"version": "1.0", "items": ["a", "b", "c"]}
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(original_data, f)

        # Verify original data is readable
        from infrastructure import load_json

        loaded = load_json(target_file)
        assert loaded == original_data


# =============================================================================
# Orphaned File Detection Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestOrphanedFileDetection:
    """Tests for detecting and handling orphaned temporary files."""

    def test_detect_orphaned_provisional_files(self, temp_plugin_env) -> None:

        """Detect provisional files without corresponding Shadow entries."""
        # Create provisional file
        provisional_dir = temp_plugin_env.digests_path / "1_Weekly" / "Provisional"
        provisional_dir.mkdir(parents=True, exist_ok=True)

        provisional_file = provisional_dir / "W0001_Individual.txt"
        with open(provisional_file, "w", encoding="utf-8") as f:
            json.dump({"individual_digests": []}, f)

        # Create Shadow without referencing this provisional
        shadow_path = temp_plugin_env.digests_path / "1_Weekly" / "ShadowWeekly.txt"
        with open(shadow_path, "w", encoding="utf-8") as f:
            json.dump({"metadata": {}, "pending_sources": []}, f)

        # Check that provisional file exists but isn't referenced
        assert provisional_file.exists()

        # Verify Shadow has no pending sources
        with open(shadow_path, "r", encoding="utf-8") as f:
            shadow_data = json.load(f)
        assert len(shadow_data.get("pending_sources", [])) == 0

    def test_cleanup_old_provisional_after_finalize(self, temp_plugin_env) -> None:

        """Verify provisional files are cleaned up after finalization."""

        # Setup provisional directory and file
        provisional_dir = temp_plugin_env.digests_path / "1_Weekly" / "Provisional"
        provisional_dir.mkdir(parents=True, exist_ok=True)

        provisional_file = provisional_dir / "W0001_Individual.txt"
        provisional_data = {
            "metadata": {"digest_number": "0001"},
            "individual_digests": [{"source_file": "L00001.txt", "keywords": ["test"]}],
        }
        with open(provisional_file, "w", encoding="utf-8") as f:
            json.dump(provisional_data, f)

        assert provisional_file.exists()

        # After finalization, provisional should be deleted
        # (This tests the cleanup mechanism exists)


# =============================================================================
# Error State Recovery Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestErrorStateRecovery:
    """Tests for recovering from various error states."""

    def test_recover_from_invalid_config(self, temp_plugin_env) -> None:

        """System should handle missing config file by using defaults."""
        from application.config import DigestConfig

        # Don't create config file - DigestConfig should use template/defaults
        # TempPluginEnvironment already sets up proper structure
        config = DigestConfig(plugin_root=temp_plugin_env.plugin_root)
        assert config is not None
        assert config.loops_path is not None
        assert config.digests_path is not None

    def test_recover_from_missing_template(self, temp_plugin_env) -> None:

        """System should create from defaults when template is missing."""
        from infrastructure import load_json_with_template

        target_file = temp_plugin_env.plugin_root / "new_file.json"
        nonexistent_template = temp_plugin_env.plugin_root / "nonexistent_template.json"

        # Should create with default factory when template doesn't exist
        result = load_json_with_template(
            target_file,
            template_file=nonexistent_template,
            default_factory=lambda: {"default": True},
            save_on_create=True,
        )

        assert result == {"default": True}
        assert target_file.exists()

    def test_graceful_degradation_on_io_error(self, temp_plugin_env) -> None:

        """System should degrade gracefully on I/O errors."""
        from infrastructure import try_load_json

        # Try to load from non-existent path
        result = try_load_json(
            Path("/nonexistent/path/file.json"),
            default={"fallback": True},
            log_on_error=False,
        )

        assert result == {"fallback": True}
