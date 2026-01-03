"""Tests for ImageSplitter."""

import pytest
from PIL import Image

from domain.constants import CELL_SIZE, EXPRESSION_CODES, GRID_COLS, GRID_ROWS
from usecases.image_splitter import ImageSplitter


class TestImageSplitter:
    """Tests for the ImageSplitter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = ImageSplitter()

    def create_test_grid(self, width: int, height: int) -> Image.Image:
        """Create a test grid image with the specified dimensions."""
        return Image.new("RGB", (width, height), color="white")

    def test_validate_correct_size(self):
        """Test validation passes for correct image size."""
        expected_width = GRID_COLS * CELL_SIZE  # 1400
        expected_height = GRID_ROWS * CELL_SIZE  # 1120

        img = self.create_test_grid(expected_width, expected_height)
        is_valid, error_msg = self.splitter.validate_image(img)

        assert is_valid is True
        assert error_msg == ""

    def test_validate_wrong_size(self):
        """Test validation fails for non-divisible image size."""
        # 101は5で割り切れないのでエラー
        img = self.create_test_grid(101, 100)
        is_valid, error_msg = self.splitter.validate_image(img)

        assert is_valid is False
        assert "not divisible" in error_msg

    def test_split_returns_20_images(self):
        """Test that split returns exactly 20 expression images."""
        expected_width = GRID_COLS * CELL_SIZE
        expected_height = GRID_ROWS * CELL_SIZE

        img = self.create_test_grid(expected_width, expected_height)
        results = self.splitter.split(img)

        assert len(results) == 20

    def test_split_returns_correct_codes(self):
        """Test that split returns all expected expression codes."""
        expected_width = GRID_COLS * CELL_SIZE
        expected_height = GRID_ROWS * CELL_SIZE

        img = self.create_test_grid(expected_width, expected_height)
        results = self.splitter.split(img)

        codes = [code for code, _ in results]
        assert codes == EXPRESSION_CODES

    def test_split_image_dimensions(self):
        """Test that each split image has correct dimensions."""
        expected_width = GRID_COLS * CELL_SIZE
        expected_height = GRID_ROWS * CELL_SIZE

        img = self.create_test_grid(expected_width, expected_height)
        results = self.splitter.split(img)

        for _code, cropped_img in results:
            assert cropped_img.width == CELL_SIZE
            assert cropped_img.height == CELL_SIZE

    def test_split_raises_for_wrong_size(self):
        """Test that split raises ValueError for non-divisible size."""
        # 101は5で割り切れないのでエラー
        img = self.create_test_grid(101, 100)

        with pytest.raises(ValueError) as exc_info:
            self.splitter.split(img)

        assert "not divisible" in str(exc_info.value)


class TestCellSizeDeprecation:
    """cell_sizeパラメータの非推奨化テスト（Stage 4: TDD）"""

    def test_cell_size_parameter_deprecated_warning(self):
        """cell_sizeパラメータ使用時に非推奨警告が出ることを確認"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _splitter = ImageSplitter(cell_size=300)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()
            assert "cell_size" in str(w[0].message)

    def test_cell_size_none_no_warning(self):
        """cell_size=Noneの場合は警告が出ないことを確認"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _splitter = ImageSplitter(cell_size=None)

            # DeprecationWarningがないことを確認
            deprecation_warnings = [
                x for x in w if issubclass(x.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) == 0

    def test_cell_size_parameter_ignored(self):
        """cell_sizeパラメータが無視されることを確認"""
        expected_width = GRID_COLS * CELL_SIZE
        expected_height = GRID_ROWS * CELL_SIZE

        img = Image.new("RGB", (expected_width, expected_height), color="white")

        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            # 異なるcell_sizeを指定しても結果は同じ
            splitter1 = ImageSplitter(cell_size=100)
            splitter2 = ImageSplitter(cell_size=500)

        result1 = splitter1.split(img)
        result2 = splitter2.split(img)

        # 両方とも同じ数の画像を生成
        assert len(result1) == len(result2) == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
