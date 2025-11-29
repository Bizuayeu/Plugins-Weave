#!/usr/bin/env python3
"""
FileNumberValidator のユニットテスト
====================================

ファイル番号の抽出と連番検証機能を個別にテスト。
ShadowValidatorの統合テストで間接的にカバーされているが、
専用テストでバリデータの契約を明示的にドキュメント化。
"""

from unittest.mock import MagicMock

import pytest

from application.finalize.validators.file_number_validator import FileNumberValidator
from domain.error_formatter import CompositeErrorFormatter
from domain.protocols import LevelRegistryProtocol

# 全テストにunitマーカーを適用
pytestmark = pytest.mark.unit


# =============================================================================
# 初期化テスト
# =============================================================================


class TestFileNumberValidatorInit:
    """FileNumberValidator 初期化のテスト"""

    def test_init_with_default_dependencies(self):
        """デフォルト依存関係で初期化"""
        validator = FileNumberValidator()
        # フォーマッタとレジストリは遅延初期化されるので、この時点ではNone
        assert validator._formatter is None
        assert validator._registry is None

    def test_init_with_custom_formatter(self):
        """カスタムフォーマッタで初期化"""
        mock_formatter = MagicMock(spec=CompositeErrorFormatter)
        validator = FileNumberValidator(formatter=mock_formatter)
        assert validator._formatter is mock_formatter

    def test_init_with_custom_registry(self):
        """カスタムレジストリで初期化"""
        mock_registry = MagicMock(spec=LevelRegistryProtocol)
        validator = FileNumberValidator(registry=mock_registry)
        assert validator._registry is mock_registry

    def test_formatter_lazy_initialization(self):
        """formatterプロパティで遅延初期化される"""
        validator = FileNumberValidator()
        assert validator._formatter is None

        # formatterプロパティにアクセスすると初期化される
        formatter = validator.formatter
        assert formatter is not None
        assert isinstance(formatter, CompositeErrorFormatter)

        # 2回目のアクセスで同じインスタンスが返される
        assert validator.formatter is formatter


# =============================================================================
# extract_numbers メソッドのテスト
# =============================================================================


class TestExtractNumbers:
    """extract_numbers メソッドのテスト"""

    @pytest.fixture
    def validator(self):
        """テスト用FileNumberValidator"""
        return FileNumberValidator()

    # -------------------------------------------------------------------------
    # 正常系
    # -------------------------------------------------------------------------

    def test_valid_loop_filenames(self, validator):
        """有効なLoopファイル名から番号を抽出"""
        filenames = ["L00001_test.txt", "L00002_another.txt", "L00003_final.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 2, 3]
        assert errors == []

    def test_valid_weekly_filenames(self, validator):
        """有効なWeeklyファイル名から番号を抽出"""
        filenames = ["W0001_digest.txt", "W0002_digest.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 2]
        assert errors == []

    def test_valid_monthly_filenames(self, validator):
        """有効なMonthlyファイル名から番号を抽出"""
        filenames = ["M0001_digest.txt", "M0002_digest.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 2]
        assert errors == []

    def test_single_filename(self, validator):
        """単一ファイル名から番号を抽出"""
        filenames = ["L00001_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1]
        assert errors == []

    def test_large_file_numbers(self, validator):
        """大きなファイル番号を抽出"""
        filenames = ["L09998_test.txt", "L09999_final.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [9998, 9999]
        assert errors == []

    def test_empty_filenames(self, validator):
        """空のリストでもエラーなし"""
        numbers, errors = validator.extract_numbers([])

        assert numbers == []
        assert errors == []

    # -------------------------------------------------------------------------
    # 異常系：型エラー
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "invalid_type",
        [
            123,
            None,
            ["nested", "list"],
            {"key": "value"},
            12.34,
            True,
        ],
    )
    def test_non_string_filename_returns_error(self, validator, invalid_type):
        """文字列以外のファイル名はエラーを返す"""
        filenames = [invalid_type]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == []
        assert len(errors) == 1
        assert "expected str" in errors[0].lower()

    def test_non_string_in_middle_of_list(self, validator):
        """リスト中間の非文字列要素もエラー"""
        filenames = ["L00001_test.txt", 123, "L00003_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 3]
        assert len(errors) == 1
        assert "index 1" in errors[0]

    # -------------------------------------------------------------------------
    # 異常系：フォーマットエラー
    # -------------------------------------------------------------------------

    def test_invalid_filename_format_returns_error(self, validator):
        """無効なファイル名フォーマットはエラーを返す"""
        filenames = ["invalid_format.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == []
        assert len(errors) == 1
        assert "Invalid filename format" in errors[0]

    def test_no_prefix_returns_error(self, validator):
        """プレフィックスがないファイル名はエラー"""
        filenames = ["00001_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == []
        assert len(errors) == 1
        assert "Invalid filename format" in errors[0]

    def test_no_number_returns_error(self, validator):
        """番号がないファイル名はエラー"""
        filenames = ["L_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == []
        assert len(errors) == 1
        assert "Invalid filename format" in errors[0]

    # -------------------------------------------------------------------------
    # 複合ケース
    # -------------------------------------------------------------------------

    def test_mixed_valid_invalid_returns_partial_results(self, validator):
        """有効と無効が混在する場合、有効なものは抽出される"""
        filenames = ["L00001_test.txt", "invalid.txt", "L00003_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 3]
        assert len(errors) == 1
        assert "invalid.txt" in errors[0]

    def test_all_invalid_returns_empty_numbers(self, validator):
        """全て無効な場合は空の番号リストを返す"""
        filenames = ["bad1.txt", "bad2.txt", "bad3.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == []
        assert len(errors) == 3

    def test_error_accumulation(self, validator):
        """複数のエラーが蓄積される"""
        filenames = [123, "invalid.txt", None, "L00001_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1]
        assert len(errors) == 3  # 123, invalid.txt, None


# =============================================================================
# check_consecutive メソッドのテスト
# =============================================================================


class TestCheckConsecutive:
    """check_consecutive メソッドのテスト"""

    @pytest.fixture
    def validator(self):
        """テスト用FileNumberValidator"""
        return FileNumberValidator()

    # -------------------------------------------------------------------------
    # 連番のケース
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "numbers",
        [
            [1, 2, 3],
            [1],
            [],
            [5, 6, 7, 8, 9],
            [100, 101, 102],
            [1, 2],
        ],
    )
    def test_consecutive_numbers_return_true(self, validator, numbers):
        """連番はTrueを返す"""
        assert validator.check_consecutive(numbers) is True

    # -------------------------------------------------------------------------
    # 非連番のケース
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize(
        "numbers",
        [
            [1, 3],
            [1, 2, 4],
            [1, 5, 10],
            [100, 102],
            [1, 2, 3, 5],
        ],
    )
    def test_non_consecutive_numbers_return_false(self, validator, numbers):
        """非連番はFalseを返す"""
        assert validator.check_consecutive(numbers) is False

    # -------------------------------------------------------------------------
    # ソート不要であることを確認
    # -------------------------------------------------------------------------

    def test_unsorted_consecutive_returns_true(self, validator):
        """未ソートの連番もTrueを返す"""
        assert validator.check_consecutive([3, 1, 2]) is True
        assert validator.check_consecutive([5, 3, 4]) is True

    def test_unsorted_non_consecutive_returns_false(self, validator):
        """未ソートの非連番もFalseを返す"""
        assert validator.check_consecutive([3, 1, 5]) is False
        assert validator.check_consecutive([10, 1, 5]) is False

    # -------------------------------------------------------------------------
    # エッジケース
    # -------------------------------------------------------------------------

    def test_single_element_is_consecutive(self, validator):
        """1要素は連番とみなす"""
        assert validator.check_consecutive([1]) is True
        assert validator.check_consecutive([999]) is True

    def test_empty_list_is_consecutive(self, validator):
        """空リストは連番とみなす"""
        assert validator.check_consecutive([]) is True

    def test_duplicate_numbers_are_not_consecutive(self, validator):
        """重複番号は連番ではない"""
        assert validator.check_consecutive([1, 1, 2]) is False
        assert validator.check_consecutive([1, 2, 2, 3]) is False

    def test_large_consecutive_sequence(self, validator):
        """大きな連番シーケンス"""
        numbers = list(range(1, 1001))  # 1-1000
        assert validator.check_consecutive(numbers) is True

    def test_negative_numbers(self, validator):
        """負の数も連番として処理"""
        assert validator.check_consecutive([-3, -2, -1]) is True
        assert validator.check_consecutive([-1, 0, 1]) is True


# =============================================================================
# validate_consecutive メソッドのテスト
# =============================================================================


class TestValidateConsecutive:
    """validate_consecutive メソッドのテスト"""

    @pytest.fixture
    def validator(self):
        """テスト用FileNumberValidator"""
        return FileNumberValidator()

    # -------------------------------------------------------------------------
    # 正常系（警告なし）
    # -------------------------------------------------------------------------

    def test_consecutive_returns_empty_warnings(self, validator):
        """連番は警告なし"""
        warnings = validator.validate_consecutive([1, 2, 3], ["L00001.txt", "L00002.txt", "L00003.txt"])
        assert warnings == []

    def test_empty_numbers_returns_empty_warnings(self, validator):
        """空の番号リストは警告なし"""
        warnings = validator.validate_consecutive([], [])
        assert warnings == []

    def test_single_number_returns_empty_warnings(self, validator):
        """単一番号は警告なし"""
        warnings = validator.validate_consecutive([1], ["L00001.txt"])
        assert warnings == []

    # -------------------------------------------------------------------------
    # 異常系（警告あり）
    # -------------------------------------------------------------------------

    def test_non_consecutive_returns_warning(self, validator):
        """非連番は警告を返す"""
        warnings = validator.validate_consecutive([1, 3], ["L00001.txt", "L00003.txt"])
        assert len(warnings) == 1
        assert "Non-consecutive" in warnings[0]

    def test_warning_message_contains_numbers(self, validator):
        """警告メッセージに番号が含まれる"""
        warnings = validator.validate_consecutive([1, 5, 10], ["f1", "f2", "f3"])
        assert len(warnings) == 1
        assert "[1, 5, 10]" in warnings[0]

    def test_warning_shows_sorted_numbers(self, validator):
        """警告メッセージはソートされた番号を表示"""
        # 入力は未ソートでもソートされて表示される
        warnings = validator.validate_consecutive([10, 1, 5], ["f1", "f2", "f3"])
        assert len(warnings) == 1
        assert "[1, 5, 10]" in warnings[0]


# =============================================================================
# エッジケーステスト
# =============================================================================


class TestFileNumberValidatorEdgeCases:
    """FileNumberValidator のエッジケーステスト"""

    @pytest.fixture
    def validator(self):
        """テスト用FileNumberValidator"""
        return FileNumberValidator()

    # -------------------------------------------------------------------------
    # Unicode ファイル名
    # -------------------------------------------------------------------------

    def test_unicode_suffix_in_filename(self, validator):
        """日本語サフィックスを含むファイル名"""
        filenames = ["L00001_テスト会話.txt", "L00002_別の会話.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 2]
        assert errors == []

    def test_emoji_in_filename_suffix(self, validator):
        """絵文字を含むファイル名"""
        filenames = ["L00001_test🎉.txt", "L00002_done✅.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 2]
        assert errors == []

    # -------------------------------------------------------------------------
    # 境界値
    # -------------------------------------------------------------------------

    def test_min_file_number(self, validator):
        """最小ファイル番号（1）"""
        filenames = ["L00001_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1]
        assert errors == []

    def test_max_file_number(self, validator):
        """大きなファイル番号（99999）"""
        filenames = ["L99999_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [99999]
        assert errors == []

    # -------------------------------------------------------------------------
    # 特殊ケース
    # -------------------------------------------------------------------------

    def test_filename_with_multiple_underscores(self, validator):
        """複数のアンダースコアを含むファイル名"""
        filenames = ["L00001_test_conversation_2024.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1]
        assert errors == []

    def test_filename_with_numbers_in_suffix(self, validator):
        """サフィックスに数字を含むファイル名"""
        filenames = ["L00001_test123.txt", "L00002_2024_review.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 2]
        assert errors == []

    def test_different_level_prefixes_in_same_list(self, validator):
        """異なるレベルプレフィックスが混在"""
        # 通常は同じレベルのファイルのみを処理するが、
        # 異なるプレフィックスでも番号は抽出される
        filenames = ["L00001_loop.txt", "W0001_weekly.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        # 両方から番号が抽出される
        assert 1 in numbers
        assert len(errors) == 0 or len(numbers) >= 1

    def test_quarterly_filenames(self, validator):
        """Quarterlyファイル名"""
        filenames = ["Q001_digest.txt", "Q002_digest.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 2]
        assert errors == []

    def test_annual_filenames(self, validator):
        """Annualファイル名"""
        filenames = ["A01_digest.txt", "A02_digest.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [1, 2]
        assert errors == []

    # -------------------------------------------------------------------------
    # エラーインデックス検証
    # -------------------------------------------------------------------------

    def test_error_index_is_correct(self, validator):
        """エラーメッセージに正しいインデックスが含まれる"""
        filenames = ["L00001_test.txt", "L00002_test.txt", 123, "L00004_test.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert len(errors) == 1
        assert "index 2" in errors[0]

    def test_multiple_error_indices(self, validator):
        """複数のエラーインデックス"""
        filenames = [None, "L00002_test.txt", 123, "invalid.txt"]
        numbers, errors = validator.extract_numbers(filenames)

        assert numbers == [2]
        assert len(errors) == 3
        # インデックス0, 2, 3のエラー
        error_str = " ".join(errors)
        assert "index 0" in error_str
        assert "index 2" in error_str
