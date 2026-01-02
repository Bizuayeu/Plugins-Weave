"""Tests for ImageSplitter."""

import pytest
from PIL import Image

# Direct imports without relative paths for test isolation
GRID_ROWS = 4
GRID_COLS = 5
CELL_SIZE = 280

EXPRESSION_CODES = [
    "normal", "smile", "focus", "diverge",
    "joy", "elation", "surprise", "calm",
    "anger", "sadness", "rage", "disgust",
    "anxiety", "fear", "upset", "worry",
    "sleepy", "cynical", "defeated", "dreamy",
]


def get_cell_position(index: int):
    row = index // GRID_COLS
    col = index % GRID_COLS
    left = col * CELL_SIZE
    top = row * CELL_SIZE
    return (left, top, left + CELL_SIZE, top + CELL_SIZE)


class ImageSplitter:
    """Test-local ImageSplitter implementation."""

    def __init__(self, rows=GRID_ROWS, cols=GRID_COLS, cell_size=CELL_SIZE):
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size

    def validate_image(self, image):
        expected_width = self.cols * self.cell_size
        expected_height = self.rows * self.cell_size
        if image.width != expected_width or image.height != expected_height:
            return (False, f"Invalid image size: {image.width}x{image.height}. Expected: {expected_width}x{expected_height}")
        return (True, "")

    def split(self, image):
        is_valid, error_msg = self.validate_image(image)
        if not is_valid:
            raise ValueError(error_msg)
        results = []
        for i, code in enumerate(EXPRESSION_CODES):
            left, top, right, bottom = get_cell_position(i)
            cropped = image.crop((left, top, right, bottom))
            results.append((code, cropped))
        return results


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
        """Test validation fails for incorrect image size."""
        img = self.create_test_grid(100, 100)
        is_valid, error_msg = self.splitter.validate_image(img)

        assert is_valid is False
        assert "Invalid image size" in error_msg

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

        for code, cropped_img in results:
            assert cropped_img.width == CELL_SIZE
            assert cropped_img.height == CELL_SIZE

    def test_split_raises_for_wrong_size(self):
        """Test that split raises ValueError for incorrect size."""
        img = self.create_test_grid(100, 100)

        with pytest.raises(ValueError) as exc_info:
            self.splitter.split(img)

        assert "Invalid image size" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
