#!/usr/bin/env python3
"""
File Naming Utilities Tests
===========================

domain/file_naming.py のテスト。
特に新規追加のユーティリティ関数をテスト。
"""
import sys
from pathlib import Path

import pytest

# 親ディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain.file_naming import (
    extract_file_number,
    extract_number_only,
    format_digest_number,
    find_max_number,
    filter_files_after,
    extract_numbers_formatted,
)


# =============================================================================
# 既存関数のテスト（回帰テスト）
# =============================================================================

class TestExtractFileNumber:
    """extract_file_number のテスト"""

    @pytest.mark.parametrize("filename,expected", [
        ("Loop0186_test.txt", ("Loop", 186)),
        ("W0001_weekly.txt", ("W", 1)),
        ("MD03_decadal.txt", ("MD", 3)),
        ("M001_monthly.txt", ("M", 1)),
        ("Q003_quarterly.txt", ("Q", 3)),
        ("A01_annual.txt", ("A", 1)),
    ])
    def test_valid_files(self, filename, expected):
        """有効なファイル名からプレフィックスと番号を抽出"""
        assert extract_file_number(filename) == expected

    @pytest.mark.parametrize("invalid_input", [
        "invalid.txt",
        None,
        123,
        "",
        "no_numbers.txt",
    ])
    def test_invalid_input(self, invalid_input):
        """無効な入力はNoneを返す"""
        assert extract_file_number(invalid_input) is None


class TestExtractNumberOnly:
    """extract_number_only のテスト"""

    def test_loop_file(self):
        """Loopファイルから番号のみを抽出"""
        assert extract_number_only("Loop0186_test.txt") == 186

    def test_invalid_input(self):
        """無効な入力はNoneを返す"""
        assert extract_number_only("invalid.txt") is None


class TestFormatDigestNumber:
    """format_digest_number のテスト"""

    @pytest.mark.parametrize("level,number,expected", [
        ("loop", 186, "Loop0186"),
        ("weekly", 1, "W0001"),
        ("monthly", 12, "M012"),
        ("quarterly", 3, "Q003"),
        ("annual", 5, "A05"),
        ("triennial", 2, "T02"),
        ("decadal", 1, "D01"),
        ("multi_decadal", 3, "MD03"),
        ("centurial", 1, "C01"),
    ])
    def test_format_levels(self, level, number, expected):
        """各レベルの番号フォーマット"""
        assert format_digest_number(level, number) == expected

    def test_invalid_level(self):
        """無効なレベルはValueErrorを発生"""
        with pytest.raises(ValueError):
            format_digest_number("invalid", 1)


# =============================================================================
# 新規追加関数のテスト
# =============================================================================

class TestFindMaxNumber:
    """find_max_number のテスト"""

    def test_find_max_from_paths(self, tmp_path):
        """Pathリストから最大番号を取得"""
        # テストファイルを作成
        files = [
            tmp_path / "W0001_test.txt",
            tmp_path / "W0003_test.txt",
            tmp_path / "W0002_test.txt",
        ]
        for f in files:
            f.touch()

        result = find_max_number(files, "W")
        assert result == 3

    def test_find_max_from_strings(self):
        """文字列リストから最大番号を取得"""
        files = ["Loop0001_a.txt", "Loop0005_b.txt", "Loop0003_c.txt"]
        result = find_max_number(files, "Loop")
        assert result == 5

    def test_empty_list(self):
        """空のリストはNoneを返す"""
        assert find_max_number([], "W") is None

    def test_no_matching_prefix(self):
        """マッチするプレフィックスがない場合はNoneを返す"""
        files = ["M001_test.txt", "M002_test.txt"]
        assert find_max_number(files, "W") is None

    def test_mixed_prefixes(self):
        """異なるプレフィックスが混在する場合"""
        files = ["W0001_a.txt", "M002_b.txt", "W0005_c.txt", "W0003_d.txt"]
        assert find_max_number(files, "W") == 5
        assert find_max_number(files, "M") == 2

    def test_multi_decadal_prefix(self):
        """MDプレフィックスの処理"""
        files = ["MD01_test.txt", "MD03_test.txt", "M002_test.txt"]
        assert find_max_number(files, "MD") == 3
        assert find_max_number(files, "M") == 2


class TestFilterFilesAfter:
    """filter_files_after のテスト"""

    def test_filter_files_after_threshold(self, tmp_path):
        """閾値より大きい番号のファイルをフィルタ"""
        files = [
            tmp_path / "Loop0001_a.txt",
            tmp_path / "Loop0003_b.txt",
            tmp_path / "Loop0005_c.txt",
            tmp_path / "Loop0002_d.txt",
        ]
        for f in files:
            f.touch()

        result = filter_files_after(files, 2)
        filenames = [f.name for f in result]

        assert len(result) == 2
        assert "Loop0003_b.txt" in filenames
        assert "Loop0005_c.txt" in filenames

    def test_filter_with_zero_threshold(self, tmp_path):
        """閾値0の場合は全ファイルを返す"""
        files = [
            tmp_path / "W0001_a.txt",
            tmp_path / "W0002_b.txt",
        ]
        for f in files:
            f.touch()

        result = filter_files_after(files, 0)
        assert len(result) == 2

    def test_filter_empty_list(self):
        """空のリストは空のリストを返す"""
        result = filter_files_after([], 5)
        assert result == []

    def test_filter_no_files_above_threshold(self, tmp_path):
        """閾値より大きいファイルがない場合"""
        files = [
            tmp_path / "Loop0001_a.txt",
            tmp_path / "Loop0002_b.txt",
        ]
        for f in files:
            f.touch()

        result = filter_files_after(files, 10)
        assert result == []


class TestExtractNumbersFormatted:
    """extract_numbers_formatted のテスト"""

    def test_extract_and_format_loop_files(self):
        """Loopファイルからフォーマット済み番号を抽出"""
        files = ["Loop0001_a.txt", "Loop0003_b.txt", "Loop0002_c.txt"]
        result = extract_numbers_formatted(files)

        assert len(result) == 3
        assert "Loop0001" in result
        assert "Loop0002" in result
        assert "Loop0003" in result

    def test_extract_and_format_weekly_files(self):
        """Weeklyファイルからフォーマット済み番号を抽出"""
        files = ["W0001_a.txt", "W0005_b.txt"]
        result = extract_numbers_formatted(files)

        assert "W0001" in result
        assert "W0005" in result

    def test_sorted_output(self):
        """結果はソートされている"""
        files = ["Loop0003_c.txt", "Loop0001_a.txt", "Loop0002_b.txt"]
        result = extract_numbers_formatted(files)

        assert result == ["Loop0001", "Loop0002", "Loop0003"]

    def test_empty_list(self):
        """空のリストは空のリストを返す"""
        result = extract_numbers_formatted([])
        assert result == []

    def test_skip_invalid_files(self):
        """無効なファイル名はスキップ"""
        files = ["Loop0001_a.txt", "invalid.txt", "Loop0002_b.txt"]
        result = extract_numbers_formatted(files)

        assert len(result) == 2
        assert "Loop0001" in result
        assert "Loop0002" in result

    def test_skip_non_string_elements(self):
        """文字列以外の要素はスキップ"""
        files = ["Loop0001_a.txt", None, 123, "Loop0002_b.txt"]
        result = extract_numbers_formatted(files)

        assert len(result) == 2


# =============================================================================
# エッジケースのテスト
# =============================================================================

class TestEdgeCases:
    """エッジケースのテスト"""

    def test_path_and_string_mixed(self, tmp_path):
        """PathオブジェクトとStringの混在"""
        file1 = tmp_path / "W0001_a.txt"
        file1.touch()
        files = [file1, "W0003_b.txt"]

        result = find_max_number(files, "W")
        assert result == 3

    def test_large_numbers(self):
        """大きな番号の処理"""
        files = ["Loop9999_a.txt", "Loop0001_b.txt"]
        assert find_max_number(files, "Loop") == 9999

    def test_leading_zeros_preserved(self):
        """ゼロ埋めが維持される"""
        files = ["W0001_test.txt"]
        result = extract_numbers_formatted(files)
        assert result == ["W0001"]
