"""Tests for domain definitions and builders modules."""

import pytest

from domain import (
    GRID_CONFIG,
    get_cell_position,
    get_cell_position_dynamic,
)


class TestGetCellPositionDynamic:
    """Tests for get_cell_position_dynamic function."""

    def test_first_cell(self):
        """動的セル位置計算: 最初のセル (index=0)"""
        result = get_cell_position_dynamic(0, cols=5, cell_width=280, cell_height=280)
        assert result == (0, 0, 280, 280)

    def test_second_cell(self):
        """動的セル位置計算: 2番目のセル (index=1)"""
        result = get_cell_position_dynamic(1, cols=5, cell_width=280, cell_height=280)
        assert result == (280, 0, 560, 280)

    def test_fifth_cell(self):
        """動的セル位置計算: 5番目のセル (index=4) - 1行目最後"""
        result = get_cell_position_dynamic(4, cols=5, cell_width=280, cell_height=280)
        assert result == (1120, 0, 1400, 280)

    def test_sixth_cell(self):
        """動的セル位置計算: 6番目のセル (index=5) - 2行目最初"""
        result = get_cell_position_dynamic(5, cols=5, cell_width=280, cell_height=280)
        assert result == (0, 280, 280, 560)

    def test_last_cell(self):
        """動的セル位置計算: 最後のセル (index=19)"""
        result = get_cell_position_dynamic(19, cols=5, cell_width=280, cell_height=280)
        assert result == (1120, 840, 1400, 1120)

    def test_custom_size(self):
        """動的セル位置計算: カスタムサイズ (100x100)"""
        result = get_cell_position_dynamic(0, cols=5, cell_width=100, cell_height=100)
        assert result == (0, 0, 100, 100)

    def test_non_square_cells(self):
        """動的セル位置計算: 非正方形セル (200x100)"""
        result = get_cell_position_dynamic(1, cols=5, cell_width=200, cell_height=100)
        assert result == (200, 0, 400, 100)

    def test_different_grid_cols(self):
        """動的セル位置計算: 異なるカラム数 (3列)"""
        result = get_cell_position_dynamic(3, cols=3, cell_width=100, cell_height=100)
        # index=3 → row=1, col=0
        assert result == (0, 100, 100, 200)


class TestGetCellPosition:
    """Tests for get_cell_position function (static wrapper)."""

    def test_first_cell(self):
        """静的セル位置計算: 最初のセル"""
        cell_size = GRID_CONFIG["cell_size"]
        result = get_cell_position(0)
        assert result == (0, 0, cell_size, cell_size)

    def test_last_cell(self):
        """静的セル位置計算: 最後のセル"""
        cols = GRID_CONFIG["cols"]
        cell_size = GRID_CONFIG["cell_size"]
        result = get_cell_position(19)
        expected_left = (19 % cols) * cell_size
        expected_top = (19 // cols) * cell_size
        assert result == (
            expected_left,
            expected_top,
            expected_left + cell_size,
            expected_top + cell_size,
        )

    def test_consistency_with_dynamic(self):
        """静的関数と動的関数の一貫性"""
        cols = GRID_CONFIG["cols"]
        cell_size = GRID_CONFIG["cell_size"]
        for i in range(20):
            static_result = get_cell_position(i)
            dynamic_result = get_cell_position_dynamic(i, cols, cell_size, cell_size)
            assert static_result == dynamic_result, f"Mismatch at index {i}"


class TestExpressionCategoryEnum:
    """ExpressionCategory Enumのテスト（Stage 7: TDD）"""

    def test_expression_category_is_enum(self):
        """ExpressionCategoryがEnumであることを確認"""
        from enum import Enum

        from domain import ExpressionCategory

        assert issubclass(ExpressionCategory, Enum)

    def test_expression_category_has_all_categories(self):
        """全カテゴリがEnumに定義されていることを確認"""
        from domain import ExpressionCategory

        expected = {"BASIC", "EMOTION", "NEGATIVE", "ANXIETY", "SPECIAL"}
        actual = {e.name for e in ExpressionCategory}

        assert actual == expected

    def test_category_codes_uses_enum(self):
        """CATEGORY_CODESがEnumをキーとして使用することを確認"""
        from domain import CATEGORY_CODES, ExpressionCategory

        assert ExpressionCategory.BASIC in CATEGORY_CODES
        assert CATEGORY_CODES[ExpressionCategory.BASIC] == ["normal", "smile", "focus", "diverge"]

    def test_category_codes_has_all_categories(self):
        """CATEGORY_CODESに全カテゴリが含まれることを確認"""
        from domain import CATEGORY_CODES, ExpressionCategory

        for category in ExpressionCategory:
            assert category in CATEGORY_CODES
            assert len(CATEGORY_CODES[category]) == 4


class TestBuildExpressionLabels:
    """build_expression_labels関数のテスト"""

    def test_default_labels_returns_dict(self):
        """デフォルトでdictを返すことを確認"""
        from domain import build_expression_labels

        result = build_expression_labels()
        assert isinstance(result, dict)

    def test_default_labels_has_20_entries(self):
        """デフォルトで20エントリを持つことを確認"""
        from domain import build_expression_labels

        result = build_expression_labels()
        assert len(result) == 20

    def test_default_labels_has_base_codes(self):
        """ベースコードのラベルが含まれることを確認"""
        from domain import build_expression_labels

        result = build_expression_labels()
        assert result["normal"] == "通常"
        assert result["joy"] == "喜び"
        assert result["anger"] == "怒り"

    def test_custom_special_codes(self):
        """カスタムSpecialコードでラベルが生成されることを確認"""
        from domain import build_expression_labels

        custom_codes = ["custom1", "custom2", "custom3", "custom4"]
        result = build_expression_labels(special_codes=custom_codes)

        # カスタムコードがラベルとして使われる（翻訳なし）
        assert result["custom1"] == "custom1"
        assert result["custom2"] == "custom2"

    def test_custom_special_codes_with_labels(self):
        """カスタムSpecialコードとラベルの両方を渡すケース"""
        from domain import build_expression_labels

        custom_codes = ["test1", "test2", "test3", "test4"]
        custom_labels = {"test1": "テスト1", "test2": "テスト2"}
        result = build_expression_labels(special_codes=custom_codes, special_labels=custom_labels)

        # ラベルが定義されているものはそれを使う
        assert result["test1"] == "テスト1"
        assert result["test2"] == "テスト2"
        # ラベルが定義されていないものはコード自体を使う
        assert result["test3"] == "test3"
        assert result["test4"] == "test4"

    def test_base_labels_unchanged_with_custom_special(self):
        """カスタムSpecialコードでもベースラベルは変わらないことを確認"""
        from domain import build_expression_labels

        custom_codes = ["x1", "x2", "x3", "x4"]
        result = build_expression_labels(special_codes=custom_codes)

        # ベースラベルは影響を受けない
        assert result["smile"] == "笑顔"
        assert result["focus"] == "思考集中"


class TestSpecialCodesConstant:
    """SPECIAL_CODES_COUNT定数のテスト（Stage 5: TDD）"""

    def test_special_codes_count_constant_exists(self):
        """SPECIAL_CODES_COUNT定数が存在することを確認"""
        from domain import SPECIAL_CODES_COUNT

        assert SPECIAL_CODES_COUNT == 4

    def test_build_expression_codes_uses_constant_in_error(self):
        """build_expression_codesのエラーメッセージにSPECIAL_CODES_COUNTが使用されることを確認"""
        from domain import SPECIAL_CODES_COUNT, build_expression_codes

        with pytest.raises(ValueError) as exc:
            build_expression_codes(["a", "b", "c"])  # 3個

        # エラーメッセージに定数値が含まれる
        assert str(SPECIAL_CODES_COUNT) in str(exc.value)

    def test_build_expression_codes_wrong_count_5(self):
        """5個のSpecialコードでエラーになることを確認"""
        from domain import build_expression_codes

        with pytest.raises(ValueError) as exc:
            build_expression_codes(["a", "b", "c", "d", "e"])  # 5個

        assert "5" in str(exc.value)


class TestBaseExpressionLabels:
    """BASE_EXPRESSION_LABELS定数のテスト（Stage 2: TDD）"""

    def test_base_expression_labels_exists(self):
        """BASE_EXPRESSION_LABELSが存在し、16個のラベルを持つことを確認"""
        from domain.definitions import BASE_EXPRESSION_LABELS

        assert len(BASE_EXPRESSION_LABELS) == 16

    def test_base_expression_labels_keys_match_codes(self):
        """BASE_EXPRESSION_LABELSのキーがBASE_EXPRESSION_CODESと一致することを確認"""
        from domain.definitions import BASE_EXPRESSION_CODES, BASE_EXPRESSION_LABELS

        assert set(BASE_EXPRESSION_CODES) == set(BASE_EXPRESSION_LABELS.keys())

    def test_base_expression_labels_no_special(self):
        """BASE_EXPRESSION_LABELSにSpecialコードが含まれないことを確認"""
        from domain.definitions import BASE_EXPRESSION_LABELS, DEFAULT_SPECIAL_CODES

        for code in DEFAULT_SPECIAL_CODES:
            assert code not in BASE_EXPRESSION_LABELS

    def test_base_expression_labels_sample_values(self):
        """BASE_EXPRESSION_LABELSのサンプル値を確認"""
        from domain.definitions import BASE_EXPRESSION_LABELS

        assert BASE_EXPRESSION_LABELS["normal"] == "通常"
        assert BASE_EXPRESSION_LABELS["joy"] == "喜び"
        assert BASE_EXPRESSION_LABELS["anger"] == "怒り"


class TestBaseExpressionCodes:
    """BASE_EXPRESSION_CODES定数のテスト（Stage 1: TDD）"""

    def test_base_expression_codes_exists(self):
        """BASE_EXPRESSION_CODESが存在し、16個のコードを持つことを確認"""
        from domain.definitions import BASE_EXPRESSION_CODES

        assert len(BASE_EXPRESSION_CODES) == 16

    def test_base_expression_codes_no_special(self):
        """BASE_EXPRESSION_CODESにSpecialコードが含まれないことを確認"""
        from domain.definitions import BASE_EXPRESSION_CODES, DEFAULT_SPECIAL_CODES

        for code in DEFAULT_SPECIAL_CODES:
            assert code not in BASE_EXPRESSION_CODES

    def test_base_expression_codes_contains_expected(self):
        """BASE_EXPRESSION_CODESに期待されるベースコードが含まれることを確認"""
        from domain.definitions import BASE_EXPRESSION_CODES

        expected_codes = [
            "normal",
            "joy",
            "anger",
            "anxiety",
            "smile",
            "elation",
            "sadness",
            "fear",
            "focus",
            "surprise",
            "rage",
            "upset",
            "diverge",
            "calm",
            "disgust",
            "worry",
        ]
        assert expected_codes == BASE_EXPRESSION_CODES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
