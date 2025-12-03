#!/usr/bin/env python3
"""
Concurrent access integration tests.

Tests that verify system behavior under concurrent access scenarios.
Note: These tests simulate concurrent access patterns, not true parallel execution.
"""

import json
import threading
import time
from pathlib import Path
from typing import List

import pytest

# =============================================================================
# Concurrent Read Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestConcurrentReads:
    """Tests for concurrent read access patterns."""

    def test_multiple_readers_same_file(self, temp_plugin_env) -> None:

        """Multiple threads should be able to read the same file concurrently."""
        # Create test file
        test_file = temp_plugin_env.digests_path / "shared_read.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        test_data = {"shared": True, "items": list(range(100))}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        results: List[dict] = []
        errors: List[Exception] = []

        def reader_task() -> None:

            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results.append(data)
            except (IOError, json.JSONDecodeError, FileNotFoundError) as e:
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

    def test_read_while_another_reads(self, temp_plugin_env) -> None:

        """Reads should not block other reads."""
        test_file = temp_plugin_env.digests_path / "concurrent_read.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        large_data = {"items": list(range(10000))}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(large_data, f)

        read_times: List[float] = []

        def timed_reader() -> None:

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

    def test_sequential_writes_preserve_data(self, temp_plugin_env) -> None:

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

    def test_append_operations_accumulate(self, temp_plugin_env) -> None:

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

    def test_simulated_write_contention(self, temp_plugin_env) -> None:

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

        def increment_task() -> None:

            try:
                with lock:  # Simulate file lock
                    with open(test_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    data["counter"] += 1
                    with open(test_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
            except (IOError, json.JSONDecodeError, KeyError, TypeError, FileNotFoundError) as e:
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

    def test_read_during_write_simulation(self, temp_plugin_env) -> None:

        """Simulate reading while another process is writing."""
        test_file = temp_plugin_env.digests_path / "read_write.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump({"version": 1}, f)

        read_results: List[dict] = []
        write_lock = threading.Lock()

        def writer_task() -> None:

            for i in range(5):
                with write_lock:
                    with open(test_file, "w", encoding="utf-8") as f:
                        json.dump({"version": i + 2}, f)
                time.sleep(0.01)

        def reader_task() -> None:

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

    def test_shadow_updates_are_idempotent(self, temp_plugin_env) -> None:

        """Multiple identical Shadow updates should produce same result."""
        shadow_path = temp_plugin_env.digests_path / "1_Weekly" / "ShadowWeekly.txt"
        shadow_path.parent.mkdir(parents=True, exist_ok=True)

        initial_shadow = {
            "metadata": {"version": "1.0"},
            "pending_sources": ["L00001.txt", "L00002.txt"],
        }

        # Write initial state
        with open(shadow_path, "w", encoding="utf-8") as f:
            json.dump(initial_shadow, f)

        # Apply same "update" multiple times
        for _ in range(5):
            with open(shadow_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Idempotent update: add L00003.txt if not present
            if "L00003.txt" not in data["pending_sources"]:
                data["pending_sources"].append("L00003.txt")

            with open(shadow_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

        # Final state should have exactly 3 entries
        with open(shadow_path, "r", encoding="utf-8") as f:
            final_data = json.load(f)

        assert len(final_data["pending_sources"]) == 3
        assert "L00003.txt" in final_data["pending_sources"]


# =============================================================================
# Race Condition Tests
# =============================================================================


@pytest.mark.integration
@pytest.mark.slow
class TestRaceConditions:
    """競合状態のテスト"""

    def test_shadow_update_atomicity(self, temp_plugin_env) -> None:

        """Shadow更新がアトミックであること - 部分書き込みが発生しない"""
        test_file = temp_plugin_env.digests_path / "atomicity_test.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # 初期データ
        initial_data = {"counter": 0, "items": list(range(100))}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        write_lock = threading.Lock()
        partial_write_detected = []
        completed_writes = []

        def atomic_writer(writer_id: int) -> None:

            """アトミックな書き込みを行う"""
            for i in range(5):
                try:
                    with write_lock:
                        with open(test_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        data["counter"] += 1
                        data["last_writer"] = writer_id
                        with open(test_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False)
                    completed_writes.append((writer_id, i))
                except (IOError, json.JSONDecodeError) as e:
                    partial_write_detected.append(e)

        # 複数スレッドで同時書き込み
        threads = [threading.Thread(target=atomic_writer, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 部分書き込みがないことを確認
        assert len(partial_write_detected) == 0, f"部分書き込み検出: {partial_write_detected}"

        # 全書き込みが完了したことを確認
        assert len(completed_writes) == 25, f"完了した書き込み: {len(completed_writes)}/25"

        # ファイルが有効なJSONであることを確認
        with open(test_file, "r", encoding="utf-8") as f:
            final_data = json.load(f)
        assert final_data["counter"] == 25

    def test_partial_write_detection(self, temp_plugin_env) -> None:

        """部分書き込みを検出できること"""
        test_file = temp_plugin_env.digests_path / "partial_write_test.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # 正常なJSONファイルを作成
        valid_data = {"complete": True, "data": "test"}
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(valid_data, f)

        # 部分的に書き込まれたファイルをシミュレート
        partial_content = '{"incomplete": true, "data": '  # 不完全なJSON
        with open(test_file, "w", encoding="utf-8") as f:
            f.write(partial_content)

        # 不完全なJSONの読み取りはエラーになるべき
        with pytest.raises(json.JSONDecodeError):
            with open(test_file, "r", encoding="utf-8") as f:
                json.load(f)

    def test_read_during_write_tracking(self, temp_plugin_env) -> None:

        """書き込み中の読み取り結果を追跡

        Note:
            このテストはタイミング依存を最小化するため、Barrierを使用して
            スレッド間の同期を確保し、読み取り成功率ではなく
            基本的な機能性をテストする。
        """
        test_file = temp_plugin_env.digests_path / "read_write_tracking.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        # 初期データ
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump({"version": 1}, f)

        read_successes: List[dict] = []
        read_failures: List[Exception] = []
        write_lock = threading.Lock()

        # Barrierで同時開始を保証
        start_barrier = threading.Barrier(2)

        def writer_task() -> None:

            start_barrier.wait()  # 両スレッドが準備完了を待つ
            for i in range(10):
                with write_lock:
                    with open(test_file, "w", encoding="utf-8") as f:
                        json.dump({"version": i + 2}, f)

        def reader_task() -> None:

            start_barrier.wait()  # 両スレッドが準備完了を待つ
            for _ in range(20):
                try:
                    with open(test_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    read_successes.append(data)
                except (IOError, json.JSONDecodeError) as e:
                    read_failures.append(e)

        writer = threading.Thread(target=writer_task)
        reader = threading.Thread(target=reader_task)

        writer.start()
        reader.start()
        writer.join()
        reader.join()

        # 少なくとも一部の読み取りが成功している
        # (全て失敗することは実際にはあり得ない)
        assert len(read_successes) > 0, "読み取りが1つも成功しませんでした"
        # 成功した読み取りは全て有効なデータ
        assert all("version" in r for r in read_successes)
        # 最終状態は正しく書き込まれている
        with open(test_file, "r", encoding="utf-8") as f:
            final_data = json.load(f)
        assert final_data["version"] == 11  # 1 + 10回の書き込み

    def test_timeout_on_blocked_operation(self, temp_plugin_env):

        """ブロックされた操作のタイムアウト動作"""
        import concurrent.futures

        test_file = temp_plugin_env.digests_path / "timeout_test.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)

        with open(test_file, "w", encoding="utf-8") as f:
            json.dump({"data": "test"}, f)

        long_running_lock = threading.Lock()
        operation_completed = []

        def long_running_task():

            """長時間実行されるタスクをシミュレート"""
            with long_running_lock:
                time.sleep(0.5)  # 500ms待機
                with open(test_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                operation_completed.append(True)
                return data

        # タイムアウト付きで実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(long_running_task)
            try:
                result = future.result(timeout=2.0)  # 2秒タイムアウト
                assert result is not None
                assert len(operation_completed) == 1
            except concurrent.futures.TimeoutError:
                pytest.fail("操作がタイムアウトしました（2秒以内に完了すべき）")
