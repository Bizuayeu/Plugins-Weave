#!/usr/bin/env python3
"""
Scale testing for EpisodicRAG.

Tests that verify system behavior with large amounts of data.
"""

import json
import time
from pathlib import Path
from typing import List

import pytest

# =============================================================================
# Fixtures for Scale Testing
# =============================================================================


@pytest.fixture
def many_loop_files(temp_plugin_env) -> List[Path]:
    """Create many Loop files for scale testing."""
    loops_path = temp_plugin_env.loops_path
    files = []

    # Create 500 Loop files (representing significant history)
    for i in range(1, 501):
        filename = f"L{i:05d}.txt"
        file_path = loops_path / filename
        content = {
            "metadata": {
                "title": f"Loop {i} - Scale Test",
                "timestamp": f"2025-01-{(i % 28) + 1:02d}T12:00:00",
                "version": "1.0",
            },
            "overall_digest": {
                "text": f"Content for Loop {i}. " * 20,
                "keywords": [f"kw{j}" for j in range(i % 10 + 1)],
            },
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False)
        files.append(file_path)

    return files


@pytest.fixture
def deep_hierarchy_setup(temp_plugin_env):
    """Setup all 8 levels of the digest hierarchy."""
    from domain.constants import LEVEL_CONFIG

    # Create directories for all levels
    for level, config in LEVEL_CONFIG.items():
        level_dir = temp_plugin_env.digests_path / config["dir"]
        level_dir.mkdir(parents=True, exist_ok=True)

        # Create Shadow file for each level
        shadow_name = f"Shadow{level.capitalize()}.txt"
        shadow_path = level_dir / shadow_name
        shadow_data = {
            "metadata": {"version": "1.0", "level": level},
            "pending_sources": [],
        }
        with open(shadow_path, "w", encoding="utf-8") as f:
            json.dump(shadow_data, f)

    return temp_plugin_env


# =============================================================================
# Large Data Volume Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestLargeDataVolumes:
    """Tests with large amounts of data."""

    def test_process_500_loops(self, many_loop_files):
        """System should handle 500+ Loop files efficiently."""
        loops_dir = many_loop_files[0].parent

        start = time.perf_counter()

        # Enumerate all Loop files
        loop_files = list(loops_dir.glob("L*.txt"))

        elapsed = time.perf_counter() - start

        assert len(loop_files) == 500
        assert elapsed < 1.0, f"Enumeration took {elapsed:.2f}s"

    def test_load_many_json_files(self, many_loop_files):
        """Loading many JSON files should be efficient."""
        start = time.perf_counter()

        loaded_count = 0
        for file_path in many_loop_files[:100]:  # Test with first 100
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "overall_digest" in data:
                loaded_count += 1

        elapsed = time.perf_counter() - start

        assert loaded_count == 100
        assert elapsed < 5.0, f"Loading 100 files took {elapsed:.2f}s"

    def test_large_digest_list_operations(self, many_loop_files):
        """Operations on large digest lists should be efficient."""
        from interfaces.provisional import DigestMerger

        # Create large digest lists
        digests_a = [
            {"source_file": f"L{i:05d}.txt", "keywords": [f"kw{i}"]} for i in range(1, 251)
        ]
        digests_b = [
            {"source_file": f"L{i:05d}.txt", "keywords": [f"new_kw{i}"]} for i in range(200, 501)
        ]

        start = time.perf_counter()

        # Merge with 50 overlapping entries
        merged = DigestMerger.merge(digests_a, digests_b)

        elapsed = time.perf_counter() - start

        # Should have 250 + 301 - 51 = 500 unique entries
        assert len(merged) == 500
        assert elapsed < 1.0, f"Merge took {elapsed:.2f}s"


# =============================================================================
# Hierarchy Depth Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestHierarchyDepth:
    """Tests for the full 8-level hierarchy."""

    def test_all_8_levels_exist(self, deep_hierarchy_setup):
        """All 8 levels should be properly set up."""
        from domain.constants import LEVEL_CONFIG

        digests_path = deep_hierarchy_setup.digests_path

        for level, config in LEVEL_CONFIG.items():
            level_dir = digests_path / config["dir"]
            assert level_dir.exists(), f"Missing level directory: {level}"

            shadow_name = f"Shadow{level.capitalize()}.txt"
            shadow_path = level_dir / shadow_name
            assert shadow_path.exists(), f"Missing Shadow for: {level}"

    def test_level_hierarchy_chain(self, deep_hierarchy_setup):
        """Verify the level hierarchy chain is complete."""
        from domain.constants import LEVEL_CONFIG

        # Build the actual chain from config
        current = "weekly"
        chain = [current]

        while LEVEL_CONFIG[current]["next"]:
            current = LEVEL_CONFIG[current]["next"]
            chain.append(current)

        # Verify chain has 8 levels and ends at centurial
        assert len(chain) == 8, f"Expected 8 levels, got {len(chain)}: {chain}"
        assert chain[0] == "weekly"
        assert chain[-1] == "centurial"

    def test_cascade_path_traversal(self, deep_hierarchy_setup):
        """Verify cascade can traverse all levels."""
        from domain.constants import LEVEL_CONFIG

        # Simulate cascade path calculation
        cascade_path = []
        current = "weekly"

        while current:
            cascade_path.append(current)
            next_level = LEVEL_CONFIG[current]["next"]
            current = next_level

        assert len(cascade_path) == 8
        assert cascade_path[0] == "weekly"
        assert cascade_path[-1] == "centurial"


# =============================================================================
# Memory Pressure Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestMemoryPressure:
    """Tests for memory usage under load."""

    def test_large_json_structure_handling(self, temp_plugin_env):
        """Handle large JSON structures without excessive memory."""
        large_file = temp_plugin_env.digests_path / "large.json"
        large_file.parent.mkdir(parents=True, exist_ok=True)

        # Create large structure
        large_data = {
            "items": [
                {
                    "id": i,
                    "content": f"Item {i} content " * 100,
                    "tags": [f"tag{j}" for j in range(20)],
                }
                for i in range(1000)
            ]
        }

        # Write large file
        with open(large_file, "w", encoding="utf-8") as f:
            json.dump(large_data, f)

        # Read it back
        with open(large_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        assert len(loaded["items"]) == 1000

    def test_iterative_processing_pattern(self, many_loop_files):
        """Process files iteratively to avoid memory accumulation."""
        processed_count = 0
        total_keywords = 0

        # Process files one at a time
        for file_path in many_loop_files[:200]:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            keywords = data.get("overall_digest", {}).get("keywords", [])
            total_keywords += len(keywords)
            processed_count += 1

            # Don't accumulate all data in memory

        assert processed_count == 200
        assert total_keywords > 0


# =============================================================================
# Throughput Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestThroughput:
    """Tests for operation throughput."""

    def test_file_creation_throughput(self, temp_plugin_env):
        """Measure file creation throughput."""
        output_dir = temp_plugin_env.digests_path / "throughput_test"
        output_dir.mkdir(parents=True, exist_ok=True)

        start = time.perf_counter()

        # Create 100 files
        for i in range(100):
            file_path = output_dir / f"file_{i:04d}.json"
            data = {"index": i, "data": f"content {i}" * 10}
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        elapsed = time.perf_counter() - start
        throughput = 100 / elapsed

        assert throughput > 50, f"Low throughput: {throughput:.1f} files/sec"
        print(f"\nFile creation throughput: {throughput:.1f} files/sec")

    def test_digest_merge_throughput(self):
        """Measure digest merge operation throughput."""
        from interfaces.provisional import DigestMerger

        # Prepare test data
        base_digests = [
            {"source_file": f"L{i:05d}.txt", "keywords": ["a", "b"]} for i in range(100)
        ]
        new_digests = [
            {"source_file": f"L{i:05d}.txt", "keywords": ["c", "d"]} for i in range(50, 150)
        ]

        start = time.perf_counter()

        # Run many merge operations
        for _ in range(1000):
            DigestMerger.merge(base_digests, new_digests)

        elapsed = time.perf_counter() - start
        throughput = 1000 / elapsed

        assert throughput > 100, f"Low merge throughput: {throughput:.1f} ops/sec"
        print(f"\nMerge throughput: {throughput:.1f} ops/sec")
