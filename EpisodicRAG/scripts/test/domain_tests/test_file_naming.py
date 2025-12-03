#!/usr/bin/env python3
"""
File Naming Utilities Tests
===========================

domain/file_naming.py のテスト。
特に新規追加のユーティリティ関数をテスト。
"""

from pathlib import Path

import pytest

from domain.file_naming import (
    extract_file_number,
    extract_number_only,
    extract_numbers_formatted,
    filter_files_after,
    find_max_number,
    format_digest_number,
)

# =============================================================================
# 既存関数のテスト（回帰テスト）
# =============================================================================


class TestExtractFileNumber:
    """extract_file_number のテスト"""

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("L00186_test.txt", ("L", 186)),
            ("W0001_weekly.txt", ("W", 1)),
            ("MD03_decadal.txt", ("MD", 3)),
            ("M0001_monthly.txt", ("M", 1)),
            ("Q003_quarterly.txt", ("Q", 3)),
            ("A001_annual.txt", ("A", 1)),
        ],
    )
    def test_valid_files(self, filename, expected) -> None:

        """有効なファイル名からプレフィックスと番号を抽出"""
        assert extract_file_number(filename) == expected

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "invalid.txt",
            None,
            123,
            "",
            "no_numbers.txt",
        ],
    )
    def test_invalid_input(self, invalid_input) -> None:

        """無効な入力はNoneを返す"""
        assert extract_file_number(invalid_input) is None


class TestExtractNumberOnly:
    """extract_number_only のテスト"""

    def test_loop_file(self) -> None:

        """Loopファイルから番号のみを抽出"""
        assert extract_number_only("L00186_test.txt") == 186

    def test_invalid_input(self) -> None:

        """無効な入力はNoneを返す"""
        assert extract_number_only("invalid.txt") is None


class TestFormatDigestNumber:
    """format_digest_number のテスト"""

    @pytest.mark.parametrize(
        "level,number,expected",
        [
            ("loop", 186, "L00186"),
            ("weekly", 1, "W0001"),
            ("monthly", 12, "M0012"),
            ("quarterly", 3, "Q003"),
            ("annual", 5, "A005"),
            ("triennial", 2, "T02"),
            ("decadal", 1, "D01"),
            ("multi_decadal", 3, "MD03"),
            ("centurial", 1, "C01"),
        ],
    )
    def test_format_levels(self, level, number, expected) -> None:

        """各レベルの番号フォーマット"""
        assert format_digest_number(level, number) == expected

    def test_invalid_level(self) -> None:

        """無効なレベルはConfigErrorを発生"""
        from domain.exceptions import ConfigError

        with pytest.raises(ConfigError):
            format_digest_number("invalid", 1)


# =============================================================================
# 新規追加関数のテスト
# =============================================================================


class TestFindMaxNumber:
    """find_max_number のテスト"""

    def test_find_max_from_paths(self, tmp_path: Path) -> None:

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

    def test_find_max_from_strings(self) -> None:

        """文字列リストから最大番号を取得"""
        files = ["L00001_a.txt", "L00005_b.txt", "L00003_c.txt"]
        result = find_max_number(files, "L")
        assert result == 5

    def test_empty_list(self) -> None:

        """空のリストはNoneを返す"""
        assert find_max_number([], "W") is None

    def test_no_matching_prefix(self) -> None:

        """マッチするプレフィックスがない場合はNoneを返す"""
        files = ["M001_test.txt", "M002_test.txt"]
        assert find_max_number(files, "W") is None

    def test_mixed_prefixes(self) -> None:

        """異なるプレフィックスが混在する場合"""
        files = ["W0001_a.txt", "M002_b.txt", "W0005_c.txt", "W0003_d.txt"]
        assert find_max_number(files, "W") == 5
        assert find_max_number(files, "M") == 2

    def test_multi_decadal_prefix(self) -> None:

        """MDプレフィックスの処理"""
        files = ["MD01_test.txt", "MD03_test.txt", "M002_test.txt"]
        assert find_max_number(files, "MD") == 3
        assert find_max_number(files, "M") == 2


class TestFilterFilesAfter:
    """filter_files_after のテスト"""

    def test_filter_files_after_threshold(self, tmp_path: Path) -> None:

        """閾値より大きい番号のファイルをフィルタ"""
        files = [
            tmp_path / "L00001_a.txt",
            tmp_path / "L00003_b.txt",
            tmp_path / "L00005_c.txt",
            tmp_path / "L00002_d.txt",
        ]
        for f in files:
            f.touch()

        result = filter_files_after(files, 2)
        filenames = [f.name for f in result]

        assert len(result) == 2
        assert "L00003_b.txt" in filenames
        assert "L00005_c.txt" in filenames

    def test_filter_with_zero_threshold(self, tmp_path: Path) -> None:

        """閾値0の場合は全ファイルを返す"""
        files = [
            tmp_path / "W0001_a.txt",
            tmp_path / "W0002_b.txt",
        ]
        for f in files:
            f.touch()

        result = filter_files_after(files, 0)
        assert len(result) == 2

    def test_filter_empty_list(self) -> None:

        """空のリストは空のリストを返す"""
        result = filter_files_after([], 5)
        assert result == []

    def test_filter_no_files_above_threshold(self, tmp_path: Path) -> None:

        """閾値より大きいファイルがない場合"""
        files = [
            tmp_path / "L00001_a.txt",
            tmp_path / "L00002_b.txt",
        ]
        for f in files:
            f.touch()

        result = filter_files_after(files, 10)
        assert result == []


class TestExtractNumbersFormatted:
    """extract_numbers_formatted のテスト"""

    def test_extract_and_format_loop_files(self) -> None:

        """Loopファイルからフォーマット済み番号を抽出"""
        files = ["L00001_a.txt", "L00003_b.txt", "L00002_c.txt"]
        result = extract_numbers_formatted(files)

        assert len(result) == 3
        assert "L00001" in result
        assert "L00002" in result
        assert "L00003" in result

    def test_extract_and_format_weekly_files(self) -> None:

        """Weeklyファイルからフォーマット済み番号を抽出"""
        files = ["W0001_a.txt", "W0005_b.txt"]
        result = extract_numbers_formatted(files)

        assert "W0001" in result
        assert "W0005" in result

    def test_sorted_output(self) -> None:

        """結果はソートされている"""
        files = ["L00003_c.txt", "L00001_a.txt", "L00002_b.txt"]
        result = extract_numbers_formatted(files)

        assert result == ["L00001", "L00002", "L00003"]

    def test_empty_list(self) -> None:

        """空のリストは空のリストを返す"""
        result = extract_numbers_formatted([])
        assert result == []

    def test_skip_invalid_files(self) -> None:

        """無効なファイル名はスキップ"""
        files = ["L00001_a.txt", "invalid.txt", "L00002_b.txt"]
        result = extract_numbers_formatted(files)

        assert len(result) == 2
        assert "L00001" in result
        assert "L00002" in result

    def test_skip_non_string_elements(self) -> None:

        """文字列以外の要素はスキップ"""
        files = ["L00001_a.txt", None, 123, "L00002_b.txt"]
        result = extract_numbers_formatted(files)

        assert len(result) == 2


# =============================================================================
# エッジケースのテスト
# =============================================================================


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_path_and_string_mixed(self, tmp_path: Path) -> None:

        """PathオブジェクトとStringの混在"""
        file1 = tmp_path / "W0001_a.txt"
        file1.touch()
        files = [file1, "W0003_b.txt"]

        result = find_max_number(files, "W")
        assert result == 3

    def test_large_numbers(self) -> None:

        """大きな番号の処理"""
        files = ["L09999_a.txt", "L00001_b.txt"]
        assert find_max_number(files, "L") == 9999

    def test_leading_zeros_preserved(self) -> None:

        """ゼロ埋めが維持される"""
        files = ["W0001_test.txt"]
        result = extract_numbers_formatted(files)
        assert result == ["W0001"]
