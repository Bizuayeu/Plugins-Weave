#!/usr/bin/env python3
"""
Property-Based Tests for File Naming
=====================================

Using hypothesis to test invariants and edge cases in file_naming.py
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from domain.constants import LEVEL_CONFIG, LEVEL_NAMES
from domain.file_naming import (
    extract_file_number,
    extract_number_only,
    extract_numbers_formatted,
    filter_files_after,
    find_max_number,
    format_digest_number,
)

# =============================================================================
# Strategies for generating valid EpisodicRAG data
# =============================================================================

# Valid level names (excluding "loop" which is special-cased)
valid_levels = st.sampled_from(LEVEL_NAMES)

# Valid level including "loop"
all_levels = st.sampled_from(LEVEL_NAMES + ["loop"])

# Arbitrary filenames (for robustness testing)
arbitrary_filenames = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S")), min_size=0, max_size=100
)

# Valid prefixes
valid_prefixes = st.sampled_from(["L", "W", "M", "Q", "A", "T", "D", "MD", "C"])


# =============================================================================
# Roundtrip Properties
# =============================================================================


class TestFileNamingRoundtrip:
    """Test roundtrip properties: format then extract"""

    @pytest.mark.property
    @given(level=all_levels, number=st.integers(min_value=0, max_value=9999))
    @settings(max_examples=200)
    def test_format_then_extract_roundtrip(self, level, number) -> None:

        """Formatting a number then extracting should yield the same number"""
        # Skip numbers too large for the level's digit count
        if level != "loop":
            config = LEVEL_CONFIG[level]
            max_val = 10 ** config["digits"] - 1
            assume(number <= max_val)

        formatted = format_digest_number(level, number)
        result = extract_file_number(formatted)

        assert result is not None, f"Failed to extract from {formatted}"
        prefix, extracted_num = result
        assert extracted_num == number, f"Expected {number}, got {extracted_num}"

    @pytest.mark.property
    @given(level=all_levels, number=st.integers(min_value=1, max_value=999))
    @settings(max_examples=100)
    def test_format_then_extract_number_only_roundtrip(self, level, number) -> None:

        """extract_number_only should yield the same number after formatting"""
        formatted = format_digest_number(level, number)
        result = extract_number_only(formatted)

        assert result == number, f"Expected {number}, got {result}"


# =============================================================================
# Robustness Properties
# =============================================================================


class TestExtractFileNumberRobustness:
    """Test that extract_file_number handles arbitrary input gracefully"""

    @pytest.mark.property
    @given(filename=arbitrary_filenames)
    @settings(max_examples=500)
    def test_never_crashes_on_arbitrary_string(self, filename) -> None:

        """extract_file_number should never raise on any string input"""
        result = extract_file_number(filename)
        # Result should be None or a valid tuple
        assert result is None or (
            isinstance(result, tuple)
            and len(result) == 2
            and isinstance(result[0], str)
            and isinstance(result[1], int)
        )

    @pytest.mark.property
    @given(
        value=st.one_of(
            st.none(),
            st.integers(),
            st.floats(allow_nan=False),
            st.lists(st.text()),
            st.dictionaries(st.text(), st.text()),
        )
    )
    @settings(max_examples=100)
    def test_handles_non_string_input(self, value) -> None:

        """extract_file_number should return None for non-string input"""
        result = extract_file_number(value)
        assert result is None


# =============================================================================
# Mathematical Properties
# =============================================================================


class TestFindMaxNumberProperties:
    """Test mathematical properties of find_max_number"""

    @pytest.mark.property
    @given(
        numbers=st.lists(st.integers(min_value=1, max_value=9999), min_size=1, max_size=20),
        prefix=valid_prefixes,
    )
    @settings(max_examples=200)
    def test_result_is_max_of_matching_files(self, numbers, prefix) -> None:

        """find_max_number should return the maximum number among matching files"""
        # Create filenames with the prefix
        files = [f"{prefix}{n:04d}_test.txt" for n in numbers]

        result = find_max_number(files, prefix)

        assert result == max(numbers), f"Expected {max(numbers)}, got {result}"

    @pytest.mark.property
    @given(files=st.lists(arbitrary_filenames, min_size=0, max_size=20))
    @settings(max_examples=100)
    def test_returns_none_or_positive_integer(self, files) -> None:

        """Result should be None or a non-negative integer"""
        result = find_max_number(files, "W")
        assert result is None or (isinstance(result, int) and result >= 0)

    @pytest.mark.property
    @given(numbers=st.lists(st.integers(min_value=1, max_value=9999), min_size=0, max_size=10))
    @settings(max_examples=100)
    def test_empty_list_returns_none(self, numbers) -> None:

        """Empty list should return None"""
        result = find_max_number([], "W")
        assert result is None


class TestFilterFilesAfterProperties:
    """Test properties of filter_files_after"""

    @pytest.mark.property
    @given(
        numbers=st.lists(st.integers(min_value=1, max_value=9999), min_size=0, max_size=20),
        threshold=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=100)
    def test_all_results_above_threshold(self, numbers, threshold) -> None:

        """All returned files should have numbers > threshold"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = [tmp_path / f"L{n:05d}_test.txt" for n in numbers]
            for f in files:
                f.touch()

            result = filter_files_after(files, threshold)

            for f in result:
                num = extract_number_only(f.name)
                assert num is not None and num > threshold

    @pytest.mark.property
    @given(
        numbers=st.lists(st.integers(min_value=1, max_value=9999), min_size=0, max_size=20),
        threshold=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=100)
    def test_result_length_invariant(self, numbers, threshold) -> None:

        """Result length should equal count of numbers > threshold"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = [tmp_path / f"L{n:05d}_test.txt" for n in numbers]
            for f in files:
                f.touch()

            result = filter_files_after(files, threshold)
            expected_count = sum(1 for n in numbers if n > threshold)

            assert len(result) == expected_count


class TestExtractNumbersFormattedProperties:
    """Test properties of extract_numbers_formatted"""

    @pytest.mark.property
    @given(numbers=st.lists(st.integers(min_value=1, max_value=9999), min_size=0, max_size=20))
    @settings(max_examples=200)
    def test_output_is_sorted(self, numbers) -> None:

        """Output should always be sorted"""
        files = [f"L{n:05d}_test.txt" for n in numbers]

        result = extract_numbers_formatted(files)

        assert result == sorted(result)

    @pytest.mark.property
    @given(
        valid_numbers=st.lists(st.integers(min_value=1, max_value=9999), min_size=0, max_size=10),
    )
    @settings(max_examples=100)
    def test_output_contains_only_valid_entries(self, valid_numbers) -> None:

        """Output should only contain formatted entries from valid input files"""
        files = [f"L{n:05d}_test.txt" for n in valid_numbers]

        result = extract_numbers_formatted(files)

        # Each result should match the formatted pattern
        for entry in result:
            # Should start with "L" and be followed by digits
            assert entry.startswith("L") or any(
                entry.startswith(LEVEL_CONFIG[lvl]["prefix"]) for lvl in LEVEL_NAMES
            )
