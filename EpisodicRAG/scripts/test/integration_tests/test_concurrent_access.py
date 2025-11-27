#!/usr/bin/env python3
"""
Concurrent access integration tests.

Tests that verify system behavior under concurrent access scenarios.
Note: These tests simulate concurrent access patterns, not true parallel execution.
"""

import json
import sys
import threading
import time
from pathlib import Path
from typing import List

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# =============================================================================
# Concurrent Read Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestConcurrentReads:
    """Tests for concurrent read access patterns."""

    def test_multiple_readers_same_file(self, temp_plugin_env):
        """Multiple threads should be able to read the same file concurrently."""
        # Create test file
        test_file = temp_plugin_env.digests_path / "shared_read.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        test_data = {"shared": True, "items": list(range(100))}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        results: List[dict] = []
        errors: List[Exception] = []

        def reader_task():
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results.append(data)
            except Exception as e:
                errors.append(e)

        # Create and start multiple reader threads
        threads = [threading.Thread(target=reader_task) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reads should succeed
        assert len(errors) == 0, f"Read errors: {errors}"
        assert len(results) == 10
        assert all(r == test_data for r in results)

    def test_read_while_another_reads(self, temp_plugin_env):
        """Reads should not block other reads."""
        test_file = temp_plugin_env.digests_path / "concurrent_read.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        large_data = {"items": list(range(10000))}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(large_data, f)

        read_times: List[float] = []

        def timed_reader():
            start = time.perf_counter()
            with open(test_file, "r", encoding="utf-8") as f:
                json.load(f)
            read_times.append(time.perf_counter() - start)

        threads = [threading.Thread(target=timed_reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reads should complete in reasonable time
        assert len(read_times) == 5
        assert all(t < 1.0 for t in read_times), f"Slow reads: {read_times}"


# =============================================================================
# Sequential Write Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestSequentialWrites:
    """Tests for sequential write access patterns."""

    def test_sequential_writes_preserve_data(self, temp_plugin_env):
        """Sequential writes should preserve data integrity."""
        test_file = temp_plugin_env.digests_path / "sequential_write.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # Write sequence of data
        for i in range(5):
            data = {"iteration": i, "timestamp": time.time()}
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(data, f)

            # Verify write
            with open(test_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            assert loaded["iteration"] == i

    def test_append_operations_accumulate(self, temp_plugin_env):
        """Append operations should accumulate data correctly."""
        from interfaces.provisional import DigestMerger

        # Simulate append-style operations
        accumulated: List[dict] = []

        for i in range(10):
            new_digest = {"source_file": f"Loop{i:04d}.txt", "iteration": i}
            accumulated = DigestMerger.merge(accumulated, [new_digest])

        assert len(accumulated) == 10
        assert all(d["source_file"] == f"Loop{i:04d}.txt" for i, d in enumerate(accumulated))


# =============================================================================
# Lock Contention Simulation Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestLockContentionSimulation:
    """Tests that simulate lock contention scenarios."""

    def test_simulated_write_contention(self, temp_plugin_env):
        """Simulate what happens when multiple processes try to write."""
        test_file = temp_plugin_env.digests_path / "contention.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize file
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump({"counter": 0}, f)

        # Simulate "atomic" read-modify-write operations
        # In reality, we'd use file locking for true concurrency
        lock = threading.Lock()
        errors: List[Exception] = []

        def increment_task():
            try:
                with lock:  # Simulate file lock
                    with open(test_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    data["counter"] += 1
                    with open(test_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment_task) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All increments should have succeeded
        assert len(errors) == 0
        with open(test_file, "r", encoding="utf-8") as f:
            final_data = json.load(f)
        assert final_data["counter"] == 10

    def test_read_during_write_simulation(self, temp_plugin_env):
        """Simulate reading while another process is writing."""
        test_file = temp_plugin_env.digests_path / "read_write.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump({"version": 1}, f)

        read_results: List[dict] = []
        write_lock = threading.Lock()

        def writer_task():
            for i in range(5):
                with write_lock:
                    with open(test_file, "w", encoding="utf-8") as f:
                        json.dump({"version": i + 2}, f)
                time.sleep(0.01)

        def reader_task():
            for _ in range(10):
                try:
                    with open(test_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    read_results.append(data)
                except json.JSONDecodeError:
                    # Might happen if we read during write
                    pass
                time.sleep(0.005)

        writer = threading.Thread(target=writer_task)
        reader = threading.Thread(target=reader_task)

        writer.start()
        reader.start()

        writer.join()
        reader.join()

        # Reader should have gotten some valid reads
        assert len(read_results) > 0
        assert all("version" in r for r in read_results)


# =============================================================================
# Shadow Update Concurrency Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestShadowUpdateConcurrency:
    """Tests for Shadow update concurrency patterns."""

    def test_shadow_updates_are_idempotent(self, temp_plugin_env):
        """Multiple identical Shadow updates should produce same result."""
        shadow_path = temp_plugin_env.digests_path / "1_Weekly" / "ShadowWeekly.txt"
        shadow_path.parent.mkdir(parents=True, exist_ok=True)

        initial_shadow = {
            "metadata": {"version": "1.0"},
            "pending_sources": ["Loop0001.txt", "Loop0002.txt"],
        }

        # Write initial state
        with open(shadow_path, "w", encoding="utf-8") as f:
            json.dump(initial_shadow, f)

        # Apply same "update" multiple times
        for _ in range(5):
            with open(shadow_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Idempotent update: add Loop0003.txt if not present
            if "Loop0003.txt" not in data["pending_sources"]:
                data["pending_sources"].append("Loop0003.txt")

            with open(shadow_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        # Final state should have exactly 3 entries
        with open(shadow_path, "r", encoding="utf-8") as f:
            final_data = json.load(f)

        assert len(final_data["pending_sources"]) == 3
        assert "Loop0003.txt" in final_data["pending_sources"]
