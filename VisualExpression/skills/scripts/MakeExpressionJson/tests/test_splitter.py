"""Tests for ImageSplitter."""

import pytest
from PIL import Image

from domain import CELL_SIZE, EXPRESSION_CODES, GRID_COLS, GRID_ROWS
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


class TestCellSizeRemoved:
    """cell_sizeパラメータ削除テスト（v2.0 TDD）"""

    def test_no_cell_size_parameter(self):
        """cell_size パラメータが存在しないことを確認"""
        import inspect

        sig = inspect.signature(ImageSplitter.__init__)
        assert "cell_size" not in sig.parameters

    def test_no_cell_size_attribute(self):
        """cell_size 属性が存在しないことを確認"""
        splitter = ImageSplitter()
        assert not hasattr(splitter, "cell_size")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
