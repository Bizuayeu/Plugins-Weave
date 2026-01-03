"""Shared pytest fixtures for MakeExpressionJson tests."""

import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image

# Add MakeExpressionJson to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain import CELL_SIZE, EXPRESSION_CODES, GRID_COLS, GRID_ROWS


@pytest.fixture
def create_test_grid_image() -> Callable[[int, int], Image.Image]:
    """
    Factory fixture to create test grid images.

    Returns:
        Function that creates RGB images with specified dimensions.
    """
    def _create_image(width: int = GRID_COLS * CELL_SIZE, height: int = GRID_ROWS * CELL_SIZE) -> Image.Image:
        return Image.new("RGB", (width, height), color="white")
    return _create_image


@pytest.fixture
def sample_template_file(tmp_path: Path) -> Path:
    """
    Create a sample HTML template with placeholder.

    Returns:
        Path to the template file.
    """
    template = tmp_path / "template.html"
    template.write_text(
        "<html><script>const IMAGES={__IMAGES_PLACEHOLDER__}</script></html>",
        encoding="utf-8"
    )
    return template


@pytest.fixture
def sample_expression_images(create_test_grid_image) -> list[tuple[str, Image.Image]]:
    """
    Create sample expression images for testing.

    Returns:
        List of (code, image) tuples for all 20 expressions.
    """
    images = []
    for code in EXPRESSION_CODES:
        img = Image.new("RGB", (CELL_SIZE, CELL_SIZE), color="gray")
        images.append((code, img))
    return images


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """
    Provide a temporary output directory.

    Returns:
        Path to a clean temporary directory.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
