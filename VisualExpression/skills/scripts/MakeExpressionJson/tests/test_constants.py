"""Tests for domain.constants module."""

import pytest

from domain.constants import (
    CELL_SIZE,
    GRID_COLS,
    GRID_ROWS,
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
        result = get_cell_position(0)
        assert result == (0, 0, CELL_SIZE, CELL_SIZE)

    def test_last_cell(self):
        """静的セル位置計算: 最後のセル"""
        result = get_cell_position(19)
        expected_left = (19 % GRID_COLS) * CELL_SIZE
        expected_top = (19 // GRID_COLS) * CELL_SIZE
        assert result == (expected_left, expected_top, expected_left + CELL_SIZE, expected_top + CELL_SIZE)

    def test_consistency_with_dynamic(self):
        """静的関数と動的関数の一貫性"""
        for i in range(20):
            static_result = get_cell_position(i)
            dynamic_result = get_cell_position_dynamic(i, GRID_COLS, CELL_SIZE, CELL_SIZE)
            assert static_result == dynamic_result, f"Mismatch at index {i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
