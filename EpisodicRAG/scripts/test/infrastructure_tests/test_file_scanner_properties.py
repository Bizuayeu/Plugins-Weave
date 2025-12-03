#!/usr/bin/env python3
"""
Property-Based Tests for File Scanner
======================================

Using hypothesis to test invariants in infrastructure/file_scanner.py

Note:
    Due to Hypothesis limitation with pytest fixtures, we use
    tempfile.TemporaryDirectory() inside tests instead of tmp_path fixture.
"""

import tempfile
from pathlib import Path
from typing import Optional

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from infrastructure.file_scanner import (
    count_files,
    filter_files_after_number,
    get_files_by_pattern,
    get_max_numbered_file,
    scan_files,
)

# =============================================================================
# Strategies for generating test data
# =============================================================================

# Safe filename characters (avoid special chars that might cause issues)
safe_chars = "abcdefghijklmnopqrstuvwxyz0123456789"

# Safe filenames
safe_filenames = st.lists(
    st.text(alphabet=safe_chars, min_size=1, max_size=15),
    min_size=0,
    max_size=20,
    unique=True,
)

# File numbers for numbered file tests
file_numbers = st.lists(
    st.integers(min_value=1, max_value=9999),
    min_size=0,
    max_size=20,
)


# =============================================================================
# scan_files Properties
# =============================================================================


class TestScanFilesProperties:
    """Property-based tests for scan_files"""

    @pytest.mark.property
    @given(filenames=safe_filenames)
    @settings(max_examples=100, deadline=None)
    def test_returns_sorted_when_sort_true(self, filenames) -> None:
        """sort=Trueでソート済み結果を返す"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for name in filenames:
                (tmp_path / f"{name}.txt").touch()

            result = scan_files(tmp_path, "*.txt", sort=True)

            assert result == sorted(result)

    @pytest.mark.property
    @given(filenames=safe_filenames)
    @settings(max_examples=100, deadline=None)
    def test_returns_correct_count(self, filenames) -> None:
        """作成したファイル数と一致"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for name in filenames:
                (tmp_path / f"{name}.txt").touch()

            result = scan_files(tmp_path, "*.txt")

            assert len(result) == len(filenames)

    @pytest.mark.property
    @given(filenames=safe_filenames)
    @settings(max_examples=50, deadline=None)
    def test_all_results_are_paths(self, filenames) -> None:
        """全結果がPathオブジェクト"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for name in filenames:
                (tmp_path / f"{name}.txt").touch()

            result = scan_files(tmp_path, "*.txt")

            for item in result:
                assert isinstance(item, Path)

    @pytest.mark.property
    def test_nonexistent_directory_returns_empty(self) -> None:
        """存在しないディレクトリは空リスト"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            nonexistent = tmp_path / "does_not_exist"
            result = scan_files(nonexistent, "*.txt")
            assert result == []

    @pytest.mark.property
    @given(
        txt_count=st.integers(min_value=0, max_value=10),
        json_count=st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=50, deadline=None)
    def test_pattern_filters_correctly(self, txt_count, json_count) -> None:
        """パターンでファイルがフィルタされる"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for i in range(txt_count):
                (tmp_path / f"file{i}.txt").touch()
            for i in range(json_count):
                (tmp_path / f"data{i}.json").touch()

            txt_result = scan_files(tmp_path, "*.txt")
            json_result = scan_files(tmp_path, "*.json")

            assert len(txt_result) == txt_count
            assert len(json_result) == json_count


# =============================================================================
# filter_files_after_number Properties
# =============================================================================


class TestFilterFilesAfterNumberProperties:
    """Property-based tests for filter_files_after_number"""

    @pytest.mark.property
    @given(
        numbers=file_numbers,
        threshold=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=200, deadline=None)
    def test_all_results_above_threshold(self, numbers, threshold) -> None:
        """thresholdより大きい番号のファイルのみ返す"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = [tmp_path / f"L{n:05d}.txt" for n in numbers]
            for f in files:
                f.touch()

            def extractor(name: str) -> Optional[int]:
                if name.startswith("L") and len(name) >= 6:
                    try:
                        return int(name[1:6])
                    except ValueError:
                        return None
                return None

            result = filter_files_after_number(files, threshold, extractor)

            for f in result:
                num = extractor(f.name)
                assert num is not None
                assert num > threshold

    @pytest.mark.property
    @given(
        numbers=file_numbers,
        threshold=st.integers(min_value=0, max_value=10000),
    )
    @settings(max_examples=100, deadline=None)
    def test_result_count_matches_expected(self, numbers, threshold) -> None:
        """結果数 == thresholdより大きい番号の数"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            files = [tmp_path / f"L{n:05d}.txt" for n in numbers]
            for f in files:
                f.touch()

            def extractor(name: str) -> Optional[int]:
                if name.startswith("L") and len(name) >= 6:
                    try:
                        return int(name[1:6])
                    except ValueError:
                        return None
                return None

            result = filter_files_after_number(files, threshold, extractor)
            expected_count = sum(1 for n in numbers if n > threshold)

            assert len(result) == expected_count

    @pytest.mark.property
    @given(threshold=st.integers(min_value=0, max_value=10000))
    @settings(max_examples=20, deadline=None)
    def test_empty_input_returns_empty(self, threshold) -> None:
        """空リスト入力は空リストを返す"""

        def extractor(name: str) -> Optional[int]:
            return None

        result = filter_files_after_number([], threshold, extractor)
        assert result == []


# =============================================================================
# count_files Properties
# =============================================================================


class TestCountFilesProperties:
    """Property-based tests for count_files"""

    @pytest.mark.property
    @given(count=st.integers(min_value=0, max_value=50))
    @settings(max_examples=50, deadline=None)
    def test_count_matches_created(self, count) -> None:
        """count_filesは作成したファイル数と一致"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for i in range(count):
                (tmp_path / f"file{i}.txt").touch()

            result = count_files(tmp_path, "*.txt")
            assert result == count

    @pytest.mark.property
    def test_nonexistent_directory_returns_zero(self) -> None:
        """存在しないディレクトリは0を返す"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            nonexistent = tmp_path / "does_not_exist"
            result = count_files(nonexistent, "*.txt")
            assert result == 0

    @pytest.mark.property
    @given(
        txt_count=st.integers(min_value=0, max_value=20),
        other_count=st.integers(min_value=0, max_value=20),
    )
    @settings(max_examples=50, deadline=None)
    def test_count_respects_pattern(self, txt_count, other_count) -> None:
        """パターンに応じた正しいカウント"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for i in range(txt_count):
                (tmp_path / f"file{i}.txt").touch()
            for i in range(other_count):
                (tmp_path / f"data{i}.json").touch()

            assert count_files(tmp_path, "*.txt") == txt_count
            assert count_files(tmp_path, "*.json") == other_count
            assert count_files(tmp_path, "*") == txt_count + other_count


# =============================================================================
# get_max_numbered_file Properties
# =============================================================================


class TestGetMaxNumberedFileProperties:
    """Property-based tests for get_max_numbered_file"""

    @pytest.mark.property
    @given(numbers=st.lists(st.integers(min_value=1, max_value=9999), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_returns_max_number(self, numbers) -> None:
        """最大番号を返す"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for n in numbers:
                (tmp_path / f"L{n:05d}.txt").touch()

            def extractor(name: str) -> Optional[int]:
                if name.startswith("L") and len(name) >= 6:
                    try:
                        return int(name[1:6])
                    except ValueError:
                        return None
                return None

            result = get_max_numbered_file(tmp_path, "L*.txt", extractor)
            assert result == max(numbers)

    @pytest.mark.property
    def test_empty_directory_returns_none(self) -> None:
        """空ディレクトリはNoneを返す"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            def extractor(name: str) -> Optional[int]:
                return None

            result = get_max_numbered_file(tmp_path, "*.txt", extractor)
            assert result is None

    @pytest.mark.property
    def test_nonexistent_directory_returns_none(self) -> None:
        """存在しないディレクトリはNoneを返す"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            nonexistent = tmp_path / "does_not_exist"

            def extractor(name: str) -> Optional[int]:
                return None

            result = get_max_numbered_file(nonexistent, "*.txt", extractor)
            assert result is None


# =============================================================================
# get_files_by_pattern Properties
# =============================================================================


class TestGetFilesByPatternProperties:
    """Property-based tests for get_files_by_pattern"""

    @pytest.mark.property
    @given(filenames=safe_filenames)
    @settings(max_examples=50, deadline=None)
    def test_returns_sorted_results(self, filenames) -> None:
        """結果は常にソート済み"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for name in filenames:
                (tmp_path / f"{name}.txt").touch()

            result = get_files_by_pattern(tmp_path, "*.txt")
            assert result == sorted(result)

    @pytest.mark.property
    @given(count=st.integers(min_value=0, max_value=20))
    @settings(max_examples=50, deadline=None)
    def test_filter_func_is_applied(self, count) -> None:
        """フィルタ関数が適用される"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            # 偶数番号と奇数番号のファイルを作成
            for i in range(count):
                (tmp_path / f"file{i}.txt").touch()

            # 偶数番号のファイルのみフィルタ
            def even_filter(p: Path) -> bool:
                # "file{n}.txt"からnを抽出
                name = p.stem  # "file{n}"
                try:
                    num = int(name[4:])
                    return num % 2 == 0
                except (ValueError, IndexError):
                    return False

            result = get_files_by_pattern(tmp_path, "*.txt", filter_func=even_filter)
            expected_count = sum(1 for i in range(count) if i % 2 == 0)

            assert len(result) == expected_count

    @pytest.mark.property
    @given(filenames=safe_filenames)
    @settings(max_examples=30, deadline=None)
    def test_no_filter_returns_all(self, filenames) -> None:
        """フィルタなしで全ファイルを返す"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            for name in filenames:
                (tmp_path / f"{name}.txt").touch()

            result = get_files_by_pattern(tmp_path, "*.txt", filter_func=None)
            assert len(result) == len(filenames)
