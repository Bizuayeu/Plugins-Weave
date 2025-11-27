#!/usr/bin/env python3
"""
test_file_scanner.py
====================

infrastructure/file_scanner.py の単体テスト。
ファイルスキャン、パターンマッチング、番号抽出機能をテスト。
"""
import pytest
from pathlib import Path
from typing import Optional

from infrastructure.file_scanner import (
    scan_files,
    get_files_by_pattern,
    get_max_numbered_file,
    filter_files_after_number,
    count_files,
)


# =============================================================================
# scan_files テスト
# =============================================================================

class TestScanFiles:
    """scan_files() 関数のテスト"""

    @pytest.mark.integration
    def test_nonexistent_directory_returns_empty(self, tmp_path):
        """存在しないディレクトリ → 空リスト"""
        nonexistent = tmp_path / "nonexistent"
        result = scan_files(nonexistent, "*.txt")
        assert result == []

    @pytest.mark.integration
    def test_empty_directory_returns_empty(self, tmp_path):
        """空ディレクトリ → 空リスト"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = scan_files(empty_dir, "*.txt")
        assert result == []

    @pytest.mark.integration
    def test_single_file_match(self, tmp_path):
        """単一ファイルマッチ"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = scan_files(tmp_path, "*.txt")
        assert len(result) == 1
        assert result[0] == test_file

    @pytest.mark.integration
    def test_multiple_files_sorted_by_default(self, tmp_path):
        """複数ファイル - デフォルトでソート"""
        (tmp_path / "c.txt").write_text("")
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")

        result = scan_files(tmp_path, "*.txt", sort=True)
        assert len(result) == 3
        assert result[0].name == "a.txt"
        assert result[1].name == "b.txt"
        assert result[2].name == "c.txt"

    @pytest.mark.integration
    def test_multiple_files_unsorted(self, tmp_path):
        """複数ファイル - ソートなし（glob順序はプラットフォーム依存）"""
        (tmp_path / "c.txt").write_text("")
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")

        result = scan_files(tmp_path, "*.txt", sort=False)
        assert len(result) == 3
        # ソートなしの場合、順序は保証されないがファイル数は正しい

    @pytest.mark.integration
    def test_pattern_filters_correctly(self, tmp_path):
        """パターンが正しくフィルタリング"""
        (tmp_path / "test.txt").write_text("")
        (tmp_path / "test.json").write_text("")
        (tmp_path / "test.md").write_text("")

        result = scan_files(tmp_path, "*.txt")
        assert len(result) == 1
        assert result[0].name == "test.txt"

    @pytest.mark.integration
    def test_glob_pattern_with_prefix(self, tmp_path):
        """プレフィックス付きglobパターン"""
        (tmp_path / "Loop0001.txt").write_text("")
        (tmp_path / "Loop0002.txt").write_text("")
        (tmp_path / "W0001.txt").write_text("")

        result = scan_files(tmp_path, "Loop*.txt")
        assert len(result) == 2


# =============================================================================
# get_files_by_pattern テスト
# =============================================================================

class TestGetFilesByPattern:
    """get_files_by_pattern() 関数のテスト"""

    @pytest.mark.integration
    def test_without_filter(self, tmp_path):
        """フィルター関数なし - 全ファイル取得"""
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")

        result = get_files_by_pattern(tmp_path, "*.txt")
        assert len(result) == 2

    @pytest.mark.integration
    def test_with_filter_matching(self, tmp_path):
        """フィルター関数 - マッチするファイルのみ"""
        (tmp_path / "keep_a.txt").write_text("")
        (tmp_path / "keep_b.txt").write_text("")
        (tmp_path / "remove_c.txt").write_text("")

        result = get_files_by_pattern(
            tmp_path,
            "*.txt",
            filter_func=lambda p: p.name.startswith("keep_")
        )
        assert len(result) == 2
        assert all("keep_" in f.name for f in result)

    @pytest.mark.integration
    def test_with_filter_no_matches(self, tmp_path):
        """フィルター関数 - 全てフィルタアウト"""
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")

        result = get_files_by_pattern(
            tmp_path,
            "*.txt",
            filter_func=lambda p: False
        )
        assert result == []

    @pytest.mark.integration
    def test_results_are_sorted(self, tmp_path):
        """結果はソート済み"""
        (tmp_path / "z.txt").write_text("")
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "m.txt").write_text("")

        result = get_files_by_pattern(tmp_path, "*.txt")
        assert result[0].name == "a.txt"
        assert result[1].name == "m.txt"
        assert result[2].name == "z.txt"


# =============================================================================
# get_max_numbered_file テスト
# =============================================================================

class TestGetMaxNumberedFile:
    """get_max_numbered_file() 関数のテスト"""

    @staticmethod
    def extract_loop_number(filename: str) -> Optional[int]:
        """Loop0001.txt → 1"""
        if filename.startswith("Loop") and filename.endswith(".txt"):
            try:
                return int(filename[4:8])
            except ValueError:
                return None
        return None

    @pytest.mark.integration
    def test_nonexistent_directory_returns_none(self, tmp_path):
        """存在しないディレクトリ → None"""
        nonexistent = tmp_path / "nonexistent"
        result = get_max_numbered_file(
            nonexistent,
            "Loop*.txt",
            self.extract_loop_number
        )
        assert result is None

    @pytest.mark.integration
    def test_empty_directory_returns_none(self, tmp_path):
        """空ディレクトリ → None"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = get_max_numbered_file(
            empty_dir,
            "Loop*.txt",
            self.extract_loop_number
        )
        assert result is None

    @pytest.mark.integration
    def test_no_matching_files_returns_none(self, tmp_path):
        """マッチするファイルなし → None"""
        (tmp_path / "other.txt").write_text("")
        result = get_max_numbered_file(
            tmp_path,
            "Loop*.txt",
            self.extract_loop_number
        )
        assert result is None

    @pytest.mark.integration
    def test_single_file_returns_number(self, tmp_path):
        """単一ファイル → その番号"""
        (tmp_path / "Loop0042.txt").write_text("")
        result = get_max_numbered_file(
            tmp_path,
            "Loop*.txt",
            self.extract_loop_number
        )
        assert result == 42

    @pytest.mark.integration
    def test_multiple_files_returns_max(self, tmp_path):
        """複数ファイル → 最大番号"""
        (tmp_path / "Loop0010.txt").write_text("")
        (tmp_path / "Loop0050.txt").write_text("")
        (tmp_path / "Loop0030.txt").write_text("")

        result = get_max_numbered_file(
            tmp_path,
            "Loop*.txt",
            self.extract_loop_number
        )
        assert result == 50

    @pytest.mark.integration
    def test_files_with_invalid_numbers_ignored(self, tmp_path):
        """無効な番号のファイルは無視"""
        (tmp_path / "Loop0020.txt").write_text("")
        (tmp_path / "LoopXXXX.txt").write_text("")
        (tmp_path / "Loop.txt").write_text("")

        result = get_max_numbered_file(
            tmp_path,
            "Loop*.txt",
            self.extract_loop_number
        )
        assert result == 20


# =============================================================================
# filter_files_after_number テスト
# =============================================================================

class TestFilterFilesAfterNumber:
    """filter_files_after_number() 関数のテスト"""

    @staticmethod
    def extract_number(filename: str) -> Optional[int]:
        """Loop0001.txt → 1"""
        if filename.startswith("Loop"):
            try:
                return int(filename[4:8])
            except ValueError:
                return None
        return None

    @pytest.mark.unit
    def test_empty_list_returns_empty(self):
        """空リスト → 空リスト"""
        result = filter_files_after_number([], 10, self.extract_number)
        assert result == []

    @pytest.mark.unit
    def test_all_below_threshold_returns_empty(self, tmp_path):
        """全てしきい値以下 → 空リスト"""
        files = [
            tmp_path / "Loop0001.txt",
            tmp_path / "Loop0005.txt",
            tmp_path / "Loop0010.txt",
        ]
        result = filter_files_after_number(files, 10, self.extract_number)
        assert result == []

    @pytest.mark.unit
    def test_all_above_threshold_returns_all(self, tmp_path):
        """全てしきい値超 → 全て返す"""
        files = [
            tmp_path / "Loop0015.txt",
            tmp_path / "Loop0020.txt",
            tmp_path / "Loop0025.txt",
        ]
        result = filter_files_after_number(files, 10, self.extract_number)
        assert len(result) == 3

    @pytest.mark.unit
    def test_mixed_files_filters_correctly(self, tmp_path):
        """混在ファイル → 正しくフィルタ"""
        files = [
            tmp_path / "Loop0005.txt",   # below
            tmp_path / "Loop0010.txt",   # equal (not above)
            tmp_path / "Loop0015.txt",   # above
            tmp_path / "Loop0020.txt",   # above
        ]
        result = filter_files_after_number(files, 10, self.extract_number)
        assert len(result) == 2
        assert all(self.extract_number(f.name) > 10 for f in result)

    @pytest.mark.unit
    def test_invalid_number_files_excluded(self, tmp_path):
        """無効な番号のファイルは除外"""
        files = [
            tmp_path / "Loop0015.txt",    # valid, above
            tmp_path / "LoopXXXX.txt",    # invalid
            tmp_path / "other.txt",       # invalid
        ]
        result = filter_files_after_number(files, 10, self.extract_number)
        assert len(result) == 1
        assert result[0].name == "Loop0015.txt"


# =============================================================================
# count_files テスト
# =============================================================================

class TestCountFiles:
    """count_files() 関数のテスト"""

    @pytest.mark.integration
    def test_nonexistent_directory_returns_zero(self, tmp_path):
        """存在しないディレクトリ → 0"""
        nonexistent = tmp_path / "nonexistent"
        result = count_files(nonexistent, "*.txt")
        assert result == 0

    @pytest.mark.integration
    def test_empty_directory_returns_zero(self, tmp_path):
        """空ディレクトリ → 0"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = count_files(empty_dir, "*.txt")
        assert result == 0

    @pytest.mark.integration
    def test_single_file_returns_one(self, tmp_path):
        """単一ファイル → 1"""
        (tmp_path / "test.txt").write_text("")
        result = count_files(tmp_path, "*.txt")
        assert result == 1

    @pytest.mark.integration
    def test_multiple_files_counted_correctly(self, tmp_path):
        """複数ファイル → 正しくカウント"""
        for i in range(5):
            (tmp_path / f"file{i}.txt").write_text("")
        result = count_files(tmp_path, "*.txt")
        assert result == 5

    @pytest.mark.integration
    def test_pattern_filters_count(self, tmp_path):
        """パターンがカウントに影響"""
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")
        (tmp_path / "c.json").write_text("")

        txt_count = count_files(tmp_path, "*.txt")
        json_count = count_files(tmp_path, "*.json")

        assert txt_count == 2
        assert json_count == 1

    @pytest.mark.integration
    def test_default_pattern_is_txt(self, tmp_path):
        """デフォルトパターンは *.txt"""
        (tmp_path / "a.txt").write_text("")
        (tmp_path / "b.txt").write_text("")
        (tmp_path / "c.json").write_text("")

        result = count_files(tmp_path)
        assert result == 2
