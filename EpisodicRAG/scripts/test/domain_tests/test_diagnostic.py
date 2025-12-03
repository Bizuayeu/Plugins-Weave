#!/usr/bin/env python3
"""
Diagnostic Context Unit Tests
=============================

Tests for domain/error_formatter/diagnostic.py
"""

from pathlib import Path

import pytest

from domain.error_formatter.diagnostic import with_diagnostic_context

# =============================================================================
# Basic Message Tests
# =============================================================================


class TestBasicMessage:
    """Basic message formatting tests"""

    def test_returns_message_only_when_no_context(self) -> None:

        """Returns original message when no context provided"""
        result = with_diagnostic_context("An error occurred")
        assert result == "An error occurred"

    def test_preserves_message_content(self) -> None:

        """Preserves the original message content"""
        msg = "Processing failed with error code 42"
        result = with_diagnostic_context(msg)
        assert msg in result


# =============================================================================
# Config Path Context Tests
# =============================================================================


class TestConfigPathContext:
    """config_path context tests"""

    def test_adds_config_path(self) -> None:

        """Adds config path to message"""
        result = with_diagnostic_context("Config error", config_path=Path("/project/config.json"))
        assert "config:" in result
        assert "config.json" in result

    def test_formats_relative_path_with_project_root(self) -> None:

        """Formats path relative to project root"""
        result = with_diagnostic_context(
            "Config error",
            config_path=Path("/project/data/config.json"),
            project_root=Path("/project"),
        )
        assert "config:" in result
        # Path should be relative
        assert "data" in result or "config.json" in result


# =============================================================================
# Current Level Context Tests
# =============================================================================


class TestCurrentLevelContext:
    """current_level context tests"""

    def test_adds_level(self) -> None:

        """Adds level to message"""
        result = with_diagnostic_context("Processing error", current_level="weekly")
        assert "level: weekly" in result

    def test_handles_various_levels(self) -> None:

        """Handles various level names"""
        for level in ["weekly", "monthly", "quarterly", "centurial"]:
            result = with_diagnostic_context("Error", current_level=level)
            assert f"level: {level}" in result


# =============================================================================
# File Count and Threshold Context Tests
# =============================================================================


class TestFileCountThresholdContext:
    """file_count and threshold context tests"""

    def test_adds_file_count_and_threshold_together(self) -> None:

        """Adds combined file count/threshold when both provided"""
        result = with_diagnostic_context("Error", file_count=3, threshold=5)
        assert "files: 3/5" in result

    def test_adds_file_count_only(self) -> None:

        """Adds file_count only when threshold not provided"""
        result = with_diagnostic_context("Error", file_count=7)
        assert "file_count: 7" in result
        assert "/" not in result.split("file_count")[1].split("|")[0]

    def test_adds_threshold_only(self) -> None:

        """Adds threshold only when file_count not provided"""
        result = with_diagnostic_context("Error", threshold=10)
        assert "threshold: 10" in result

    def test_handles_zero_file_count(self) -> None:

        """Handles zero file count"""
        result = with_diagnostic_context("Error", file_count=0, threshold=5)
        assert "files: 0/5" in result


# =============================================================================
# Last Operation Context Tests
# =============================================================================


class TestLastOperationContext:
    """last_operation context tests"""

    def test_adds_operation(self) -> None:

        """Adds operation to message"""
        result = with_diagnostic_context("Error", last_operation="load_config")
        assert "operation: load_config" in result

    def test_handles_various_operations(self) -> None:

        """Handles various operation names"""
        operations = ["save_digest", "cascade_update", "validate_shadow", "cleanup"]
        for op in operations:
            result = with_diagnostic_context("Error", last_operation=op)
            assert f"operation: {op}" in result


# =============================================================================
# Multiple Context Combination Tests
# =============================================================================


class TestMultipleContexts:
    """Multiple context combination tests"""

    def test_combines_all_contexts(self) -> None:

        """Combines all context types in message"""
        result = with_diagnostic_context(
            "Critical error",
            config_path=Path("/project/config.json"),
            current_level="weekly",
            file_count=3,
            threshold=5,
            last_operation="finalize",
            project_root=Path("/project"),
        )

        assert "Critical error" in result
        assert "config:" in result
        assert "level: weekly" in result
        assert "files: 3/5" in result
        assert "operation: finalize" in result

    def test_uses_pipe_separator(self) -> None:

        """Uses pipe separator between context parts"""
        result = with_diagnostic_context("Error", current_level="weekly", last_operation="save")
        assert " | " in result

    def test_maintains_order(self) -> None:

        """Maintains consistent order of context parts"""
        result = with_diagnostic_context(
            "Error",
            config_path=Path("/config.json"),
            current_level="weekly",
            file_count=3,
            threshold=5,
            last_operation="save",
        )

        parts = result.split(" | ")
        assert parts[0] == "Error"
        # Config should come before level
        config_idx = next(i for i, p in enumerate(parts) if "config:" in p)
        level_idx = next(i for i, p in enumerate(parts) if "level:" in p)
        assert config_idx < level_idx


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestEdgeCases:
    """Edge case tests"""

    def test_empty_message(self) -> None:

        """Handles empty message"""
        result = with_diagnostic_context("", current_level="weekly")
        assert "level: weekly" in result

    def test_message_with_special_characters(self) -> None:

        """Handles message with special characters"""
        msg = "Error: file 'test.json' not found (code: 404)"
        result = with_diagnostic_context(msg, current_level="weekly")
        assert msg in result

    def test_unicode_in_message(self) -> None:

        """Handles unicode in message"""
        msg = "エラー: ファイルが見つかりません"
        result = with_diagnostic_context(msg, current_level="weekly")
        assert msg in result

    def test_very_long_message(self) -> None:

        """Handles very long message"""
        long_msg = "Error: " + "x" * 1000
        result = with_diagnostic_context(long_msg, current_level="weekly")
        assert long_msg in result

    def test_none_values_are_ignored(self) -> None:

        """None values don't add context"""
        result = with_diagnostic_context(
            "Error",
            config_path=None,
            current_level=None,
            file_count=None,
            threshold=None,
            last_operation=None,
        )
        assert result == "Error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
