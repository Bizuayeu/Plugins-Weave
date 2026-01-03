"""Tests for GridLayout dataclass."""

import pytest

from domain.grid_layout import GridLayout


class TestGridLayoutCreation:
    """GridLayout 生成テスト"""

    def test_default_factory(self):
        """デフォルトファクトリで標準設定のGridLayoutを生成"""
        layout = GridLayout.default()

        assert layout.rows == 4
        assert layout.cols == 5
        assert layout.cell_size == 280
        assert len(layout.expression_codes) == 20

    def test_custom_creation(self):
        """カスタムパラメータでGridLayoutを生成"""
        layout = GridLayout(
            rows=2,
            cols=3,
            cell_size=100,
            expression_codes=("a", "b", "c", "d", "e", "f"),
        )

        assert layout.rows == 2
        assert layout.cols == 3
        assert layout.cell_size == 100
        assert len(layout.expression_codes) == 6

    def test_immutable(self):
        """GridLayoutはイミュータブル（frozen=True）"""
        layout = GridLayout.default()

        with pytest.raises(AttributeError):
            layout.rows = 10  # type: ignore


class TestGridLayoutCellPosition:
    """セル位置計算テスト"""

    def test_first_cell(self):
        """最初のセル（index=0）の位置"""
        layout = GridLayout.default()
        pos = layout.get_cell_position(0)
        assert pos == (0, 0, 280, 280)

    def test_second_cell(self):
        """2番目のセル（index=1）の位置"""
        layout = GridLayout.default()
        pos = layout.get_cell_position(1)
        assert pos == (280, 0, 560, 280)

    def test_first_row_last_cell(self):
        """1行目最後のセル（index=4）の位置"""
        layout = GridLayout.default()
        pos = layout.get_cell_position(4)
        assert pos == (1120, 0, 1400, 280)

    def test_second_row_first_cell(self):
        """2行目最初のセル（index=5）の位置"""
        layout = GridLayout.default()
        pos = layout.get_cell_position(5)
        assert pos == (0, 280, 280, 560)

    def test_last_cell(self):
        """最後のセル（index=19）の位置"""
        layout = GridLayout.default()
        pos = layout.get_cell_position(19)
        assert pos == (1120, 840, 1400, 1120)

    def test_custom_cell_size(self):
        """カスタムセルサイズでの位置計算"""
        layout = GridLayout(rows=4, cols=5, cell_size=100, expression_codes=tuple(range(20)))
        pos = layout.get_cell_position(0)
        assert pos == (0, 0, 100, 100)


class TestGridLayoutExpressionAt:
    """expression_at メソッドテスト"""

    def test_first_expression(self):
        """(row=0, col=0) は 'normal'"""
        layout = GridLayout.default()
        assert layout.expression_at(row=0, col=0) == "normal"

    def test_special_column(self):
        """(row=0, col=4) は 'sleepy'（Special列）"""
        layout = GridLayout.default()
        assert layout.expression_at(row=0, col=4) == "sleepy"

    def test_second_row_first(self):
        """(row=1, col=0) は 'smile'"""
        layout = GridLayout.default()
        assert layout.expression_at(row=1, col=0) == "smile"

    def test_last_expression(self):
        """(row=3, col=4) は 'dreamy'"""
        layout = GridLayout.default()
        assert layout.expression_at(row=3, col=4) == "dreamy"


class TestGridLayoutValidation:
    """画像サイズ検証テスト"""

    def test_valid_dimensions(self):
        """正しいサイズ (1400x1120) は有効"""
        layout = GridLayout.default()
        is_valid, msg = layout.validate_dimensions(1400, 1120)
        assert is_valid is True
        assert msg == ""

    def test_width_not_divisible(self):
        """幅が列数で割り切れない場合は無効"""
        layout = GridLayout.default()
        is_valid, msg = layout.validate_dimensions(1401, 1120)
        assert is_valid is False
        assert "not divisible" in msg

    def test_height_not_divisible(self):
        """高さが行数で割り切れない場合は無効"""
        layout = GridLayout.default()
        is_valid, msg = layout.validate_dimensions(1400, 1121)
        assert is_valid is False
        assert "not divisible" in msg

    def test_smaller_valid_dimensions(self):
        """小さくても割り切れるサイズは有効 (700x560)"""
        layout = GridLayout.default()
        is_valid, _msg = layout.validate_dimensions(700, 560)
        assert is_valid is True


class TestGridLayoutWithSpecialCodes:
    """カスタムSpecialコード対応テスト"""

    def test_with_custom_special_codes(self):
        """カスタムSpecialコードでGridLayoutを生成"""
        layout = GridLayout.with_special_codes(["wink", "pout", "smug", "starry"])

        assert layout.rows == 4
        assert layout.cols == 5
        # Special codes are at positions 4, 9, 14, 19
        codes = layout.expression_codes
        assert codes[4] == "wink"
        assert codes[9] == "pout"
        assert codes[14] == "smug"
        assert codes[19] == "starry"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
