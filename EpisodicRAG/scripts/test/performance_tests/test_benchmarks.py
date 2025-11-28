#!/usr/bin/env python3
"""
Performance benchmarks for EpisodicRAG.

Tests that measure execution time for critical operations.
Run with: pytest -m performance --no-cov -v

These tests are marked as 'slow' and 'performance' and are skipped by default.
To run: pytest scripts/test/performance_tests/ -v --no-cov
"""

import json
import time
from pathlib import Path
from typing import List

import pytest

from domain.constants import LEVEL_CONFIG

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def large_loop_files(temp_plugin_env) -> List[Path]:
    """Create a large number of Loop files for performance testing."""
    loops_path = temp_plugin_env.loops_path
    files = []

    # Create 100 Loop files
    for i in range(1, 101):
        filename = f"L{i:05d}.txt"
        file_path = loops_path / filename
        content = {
            "metadata": {
                "title": f"Test Loop {i}",
                "timestamp": "2025-01-01T00:00:00",
                "version": "1.0",
            },
            "overall_digest": {
                "text": f"This is the overall digest for Loop {i}. " * 10,
                "keywords": [f"keyword{j}" for j in range(10)],
            },
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        files.append(file_path)

    return files


@pytest.fixture
def large_individual_digests() -> List[dict]:
    """Create a large list of individual digests for performance testing."""
    return [
        {
            "source_file": f"L{i:05d}.txt",
            "keywords": [f"keyword{j}" for j in range(5)],
            "summary": f"Summary for Loop {i}. " * 5,
        }
        for i in range(1, 501)
    ]


# =============================================================================
# JSON I/O Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestJsonIOPerformance:
    """Performance tests for JSON I/O operations."""

    def test_json_load_performance(self, large_loop_files):
        """JSON loading should be fast for typical file sizes."""
        start = time.perf_counter()

        for file_path in large_loop_files:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)

        elapsed = time.perf_counter() - start

        # 100 files should load in under 2 seconds
        assert elapsed < 2.0, f"JSON loading took {elapsed:.2f}s for 100 files"
        print(f"\nJSON load: {elapsed:.3f}s for {len(large_loop_files)} files")

    def test_json_dump_performance(self, temp_plugin_env, large_individual_digests):
        """JSON dumping should be fast for typical data sizes."""
        output_path = temp_plugin_env.digests_path / "performance_test.json"

        start = time.perf_counter()

        data = {
            "metadata": {"version": "1.0"},
            "individual_digests": large_individual_digests,
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        elapsed = time.perf_counter() - start

        # Writing 500 digests should take under 1 second
        assert elapsed < 1.0, f"JSON dump took {elapsed:.2f}s"
        print(f"\nJSON dump: {elapsed:.3f}s for {len(large_individual_digests)} digests")


# =============================================================================
# File Scanning Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestFileScanningPerformance:
    """Performance tests for file scanning operations."""

    def test_glob_performance(self, large_loop_files):
        """Glob pattern matching should be fast."""
        loops_dir = large_loop_files[0].parent

        start = time.perf_counter()

        # Run glob 10 times to get stable measurement
        for _ in range(10):
            files = list(loops_dir.glob("L*.txt"))

        elapsed = time.perf_counter() - start

        # 10 iterations of glob should complete in under 1 second
        assert elapsed < 1.0, f"Glob took {elapsed:.2f}s for 10 iterations"
        assert len(files) == 100
        print(f"\nGlob: {elapsed:.3f}s for 10 iterations (100 files each)")

    def test_file_enumeration_performance(self, large_loop_files):
        """Directory enumeration should be fast."""
        loops_dir = large_loop_files[0].parent

        start = time.perf_counter()

        # Enumerate and filter files
        for _ in range(10):
            _ = [f for f in loops_dir.iterdir() if f.suffix == ".txt"]

        elapsed = time.perf_counter() - start

        assert elapsed < 1.0, f"File enumeration took {elapsed:.2f}s"
        print(f"\nEnumeration: {elapsed:.3f}s for 10 iterations")


# =============================================================================
# Digest Merging Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestDigestMergingPerformance:
    """Performance tests for digest merging operations."""

    def test_merge_performance(self, large_individual_digests):
        """Merging large digest lists should be fast."""
        from interfaces.provisional import DigestMerger

        # Create two lists to merge
        existing = large_individual_digests[:250]
        new_digests = large_individual_digests[200:]  # 50 overlapping

        start = time.perf_counter()

        # Run merge 100 times
        for _ in range(100):
            result = DigestMerger.merge(existing, new_digests)

        elapsed = time.perf_counter() - start

        # 100 merges should complete in under 2 seconds
        assert elapsed < 2.0, f"Merge took {elapsed:.2f}s for 100 iterations"
        assert len(result) == 500  # 250 + 300 - 50 overlap
        print(f"\nMerge: {elapsed:.3f}s for 100 iterations (250+300 digests)")


# =============================================================================
# Level Configuration Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestLevelConfigPerformance:
    """Performance tests for level configuration lookups."""

    def test_level_config_lookup_performance(self):
        """Level config lookups should be instant."""
        levels = list(LEVEL_CONFIG.keys())

        start = time.perf_counter()

        # Run 10000 lookups
        for _ in range(10000):
            for level in levels:
                _ = LEVEL_CONFIG[level]

        elapsed = time.perf_counter() - start

        # 10000 * 8 lookups should complete in under 0.1 seconds
        assert elapsed < 0.1, f"Config lookup took {elapsed:.2f}s"
        print(f"\nConfig lookup: {elapsed:.6f}s for {10000 * len(levels)} lookups")


# =============================================================================
# Input Loading Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestInputLoadingPerformance:
    """Performance tests for input loading operations."""

    def test_json_string_parsing_performance(self, large_individual_digests):
        """JSON string parsing should be fast."""
        from interfaces.provisional import InputLoader

        # Create a large JSON string
        json_string = json.dumps(large_individual_digests)

        start = time.perf_counter()

        # Parse 100 times
        for _ in range(100):
            result = InputLoader.load(json_string)

        elapsed = time.perf_counter() - start

        # 100 parses should complete in under 5 seconds
        assert elapsed < 5.0, f"JSON parsing took {elapsed:.2f}s for 100 iterations"
        assert len(result) == 500
        print(f"\nJSON parse: {elapsed:.3f}s for 100 iterations (500 digests)")


# =============================================================================
# Memory Usage Estimation
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryEstimation:
    """Rough memory usage estimation tests."""

    def test_digest_list_memory(self, large_individual_digests):
        """Estimate memory usage for digest lists."""
        import sys

        # Get rough size estimate
        size_bytes = sys.getsizeof(large_individual_digests)

        # Each digest has additional overhead
        for d in large_individual_digests[:10]:
            size_bytes += sys.getsizeof(d)

        print(f"\nEstimated memory: ~{size_bytes / 1024:.1f} KB for base list")
        print(f"Digests count: {len(large_individual_digests)}")

        # List of 500 digests should be reasonably small
        # This is a rough estimate - actual memory usage is higher
        assert size_bytes < 1024 * 1024  # Less than 1MB for base structure
