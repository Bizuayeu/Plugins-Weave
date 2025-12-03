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
from typing import TYPE_CHECKING, List

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

from domain.constants import LEVEL_CONFIG

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def large_loop_files(temp_plugin_env: "TempPluginEnvironment") -> List[Path]:
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

    def test_json_load_performance(self, large_loop_files) -> None:
        """JSON loading should be fast for typical file sizes."""
        start = time.perf_counter()

        for file_path in large_loop_files:
            with open(file_path, "r", encoding="utf-8") as f:
                json.load(f)

        elapsed = time.perf_counter() - start

        # 100 files should load in under 2 seconds
        assert elapsed < 2.0, f"JSON loading took {elapsed:.2f}s for 100 files"
        print(f"\nJSON load: {elapsed:.3f}s for {len(large_loop_files)} files")

    def test_json_dump_performance(
        self, temp_plugin_env: "TempPluginEnvironment", large_individual_digests
    ) -> None:
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

    def test_glob_performance(self, large_loop_files) -> None:
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

    def test_file_enumeration_performance(self, large_loop_files) -> None:
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

    def test_merge_performance(self, large_individual_digests) -> None:
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

    def test_level_config_lookup_performance(self) -> None:
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

    def test_json_string_parsing_performance(self, large_individual_digests) -> None:
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

    def test_digest_list_memory(self, large_individual_digests) -> None:
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
        # Lower bound: ensure logic is actually running (not empty structure)
        assert size_bytes > 1024, "Memory too small - logic may not be running"
        # Upper bound: should not exceed 1MB for base structure
        assert size_bytes < 1024 * 1024, "Memory exceeds 1MB limit"
        # Per-digest memory ratio check
        per_digest_bytes = size_bytes / len(large_individual_digests)
        assert 10 < per_digest_bytes < 10000, (
            f"Per-digest memory {per_digest_bytes:.1f}B out of expected range (10-10000B)"
        )


# =============================================================================
# File Detection Performance Tests
# =============================================================================


@pytest.fixture
def large_digest_files(temp_plugin_env: "TempPluginEnvironment") -> List[Path]:
    """Create a large number of Digest files for performance testing."""
    weekly_dir = temp_plugin_env.digests_path / "1_Weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)
    files = []

    # Create 1000 digest files
    for i in range(1, 1001):
        filename = f"W{i:04d}_TestDigest.txt"
        file_path = weekly_dir / filename
        content = {
            "metadata": {"digest_number": f"{i:04d}", "level": "weekly"},
            "overall_digest": {"keywords": ["test"]},
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f)
        files.append(file_path)

    return files


@pytest.mark.performance
@pytest.mark.slow
class TestFileDetectionPerformance:
    """Performance tests for file detection operations."""

    def test_find_new_files_1000(
        self, large_digest_files, digest_config: "DigestConfig", times_tracker: "DigestTimesTracker"
    ) -> None:
        """File detection should handle 1000 files efficiently."""
        from application.shadow import FileDetector

        detector = FileDetector(digest_config, times_tracker)

        start = time.perf_counter()

        # Run file detection 10 times
        for _ in range(10):
            detector.find_new_files("monthly")

        elapsed = time.perf_counter() - start

        # Lower bound: ensure detection logic is actually executing
        assert elapsed > 0.01, "Detection too fast - check if logic is executing"
        # Upper bound: 10 iterations should complete in under 5 seconds
        assert elapsed < 5.0, f"File detection took {elapsed:.2f}s for 10 iterations (max 5s)"
        # Performance rate check: ensure minimum throughput
        files_per_second = (1000 * 10) / elapsed  # 1000 files × 10 iterations
        assert files_per_second > 100, (
            f"Detection rate {files_per_second:.0f} files/sec below minimum (100 files/sec)"
        )
        print(f"\nFile detection: {elapsed:.3f}s for 10 iterations (1000 files)")


# =============================================================================
# Shadow I/O Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestShadowIOPerformance:
    """Performance tests for Shadow I/O operations."""

    def test_shadow_load_save_cycle(
        self,
        temp_plugin_env: "TempPluginEnvironment",
        template: "ShadowTemplate",
        shadow_io: "ShadowIO",
    ) -> None:
        """Shadow load/save cycle should be fast."""
        start = time.perf_counter()

        # Run load/save cycle 100 times
        for i in range(100):
            data = shadow_io.load_or_create()
            # Modify slightly to trigger save
            data["metadata"]["test_iteration"] = i
            shadow_io.save(data)

        elapsed = time.perf_counter() - start

        # 100 load/save cycles should complete in under 10 seconds
        assert elapsed < 10.0, f"Shadow I/O took {elapsed:.2f}s for 100 cycles"
        print(f"\nShadow I/O: {elapsed:.3f}s for 100 load/save cycles")


# =============================================================================
# Regex Extraction Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestRegexPerformance:
    """Performance tests for regex-based file name extraction."""

    def test_extract_file_number_1000(self) -> None:
        """Regex extraction should be fast for many files."""
        from domain.file_naming import extract_file_number

        # Create 1000 file names
        filenames = [f"L{i:05d}_TestLoop.txt" for i in range(1, 1001)]

        start = time.perf_counter()

        # Extract numbers 10 times
        for _ in range(10):
            results = [extract_file_number(f) for f in filenames]

        elapsed = time.perf_counter() - start

        # 10000 extractions should complete in under 0.5 seconds
        assert elapsed < 0.5, f"Regex extraction took {elapsed:.2f}s"
        assert all(r is not None for r in results)
        print(f"\nRegex extraction: {elapsed:.3f}s for 10000 extractions")


# =============================================================================
# Grand Digest Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestGrandDigestPerformance:
    """Performance tests for Grand Digest operations."""

    def test_grand_digest_crud_cycle(
        self, temp_plugin_env: "TempPluginEnvironment", digest_config: "DigestConfig"
    ) -> None:
        """Grand Digest CRUD operations should be fast."""
        from application.grand import GrandDigestManager

        manager = GrandDigestManager(digest_config)

        start = time.perf_counter()

        # Run CRUD cycle 50 times
        for i in range(50):
            manager.load_or_create()
            # Update digest - signature: (level, digest_name, overall_digest)
            overall_digest = {
                "name": f"TestDigest_{i}",
                "source_files": [f"W{j:04d}.txt" for j in range(1, 6)],
                "keywords": ["test", "performance"],
                "abstract": "Test abstract",
                "impression": "Test impression",
            }
            manager.update_digest("weekly", f"W{i:04d}_Test", overall_digest)

        elapsed = time.perf_counter() - start

        # 50 CRUD cycles should complete in under 5 seconds
        assert elapsed < 5.0, f"Grand Digest CRUD took {elapsed:.2f}s for 50 cycles"
        print(f"\nGrand Digest CRUD: {elapsed:.3f}s for 50 cycles")


# =============================================================================
# Cascade Processing Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestCascadePerformance:
    """Performance tests for cascade processing operations."""

    def test_cascade_initialization(
        self, temp_plugin_env: "TempPluginEnvironment", digest_config: "DigestConfig"
    ) -> None:
        """Cascade component initialization should be fast."""
        from application.grand import ShadowGrandDigestManager
        from application.tracking import DigestTimesTracker

        start = time.perf_counter()

        # Initialize components 20 times
        for _ in range(20):
            DigestTimesTracker(digest_config)
            ShadowGrandDigestManager(digest_config)
            # ShadowGrandDigestManager contains ShadowUpdater internally

        elapsed = time.perf_counter() - start

        # 20 initializations should complete in under 2 seconds
        assert elapsed < 2.0, f"Cascade init took {elapsed:.2f}s for 20 iterations"
        print(f"\nCascade init: {elapsed:.3f}s for 20 iterations")


# =============================================================================
# File Appending Performance Tests
# =============================================================================


@pytest.mark.performance
@pytest.mark.slow
class TestFileAppendingPerformance:
    """Performance tests for file appending operations."""

    def test_add_files_to_shadow_50(
        self, temp_plugin_env: "TempPluginEnvironment", digest_config: "DigestConfig"
    ) -> None:
        """Adding 50 files to shadow should be fast."""
        from application.grand import ShadowGrandDigestManager

        # Create 50 mock files
        loops_path = temp_plugin_env.loops_path
        for i in range(1, 51):
            file_path = loops_path / f"L{i:05d}_Test.txt"
            file_path.write_text('{"overall_digest": {"keywords": ["test"]}}')

        start = time.perf_counter()

        # Run update_shadow_for_new_loops 10 times
        for _ in range(10):
            shadow_manager = ShadowGrandDigestManager(digest_config)
            shadow_manager.clear_shadow_level("weekly")
            # Use the public API for detecting and adding new files
            shadow_manager.update_shadow_for_new_loops()

        elapsed = time.perf_counter() - start

        # 10 iterations of updating shadow should complete in under 10 seconds
        assert elapsed < 10.0, f"Shadow update took {elapsed:.2f}s for 10 iterations"
        print(f"\nShadow update: {elapsed:.3f}s for 10 iterations (50 files)")
