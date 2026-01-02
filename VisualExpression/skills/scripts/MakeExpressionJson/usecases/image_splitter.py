"""Image splitting logic for expression grids."""

from typing import List, Tuple, Optional
from PIL import Image

try:
    from ..domain.constants import EXPRESSION_CODES, GRID_COLS, GRID_ROWS, CELL_SIZE, build_expression_codes
except ImportError:
    from domain.constants import EXPRESSION_CODES, GRID_COLS, GRID_ROWS, CELL_SIZE, build_expression_codes


class ImageSplitter:
    """Splits a grid image into individual expression images."""

    def __init__(
        self,
        rows: int = GRID_ROWS,
        cols: int = GRID_COLS,
        cell_size: Optional[int] = None,
        output_size: int = CELL_SIZE,
        auto_detect: bool = True,
        special_codes: Optional[List[str]] = None,
    ):
        """
        Initialize the image splitter.

        Args:
            rows: Number of rows in the grid (default: 4)
            cols: Number of columns in the grid (default: 5)
            cell_size: Size of each cell in pixels (None = auto-detect from image)
            output_size: Output size for each cropped image (default: 280)
            auto_detect: If True, auto-detect cell size from image dimensions
            special_codes: Custom Special category codes (4 items). None = use defaults.
        """
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        self.output_size = output_size
        self.auto_detect = auto_detect
        self.expression_codes = build_expression_codes(special_codes)

    def _get_cell_position(self, index: int, cell_width: int, cell_height: int) -> Tuple[int, int, int, int]:
        """Get pixel coordinates for a cell at the given index."""
        row = index // self.cols
        col = index % self.cols
        left = col * cell_width
        top = row * cell_height
        return (left, top, left + cell_width, top + cell_height)

    def validate_image(self, image: Image.Image) -> Tuple[bool, str]:
        """
        Validate that the image can be split into the expected grid.

        Args:
            image: PIL Image object

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if dimensions are divisible by grid size
        if image.width % self.cols != 0:
            return (False, f"Image width {image.width} is not divisible by {self.cols} columns")
        if image.height % self.rows != 0:
            return (False, f"Image height {image.height} is not divisible by {self.rows} rows")

        return (True, "")

    def split(self, image: Image.Image) -> List[Tuple[str, Image.Image]]:
        """
        Split a grid image into individual expression images.

        Args:
            image: PIL Image containing the expression grid

        Returns:
            List of (expression_code, cropped_image) tuples

        Raises:
            ValueError: If the image dimensions are invalid
        """
        is_valid, error_msg = self.validate_image(image)
        if not is_valid:
            raise ValueError(error_msg)

        # Calculate cell size from image dimensions
        cell_width = image.width // self.cols
        cell_height = image.height // self.rows

        results: List[Tuple[str, Image.Image]] = []

        for i, code in enumerate(self.expression_codes):
            left, top, right, bottom = self._get_cell_position(i, cell_width, cell_height)
            cropped = image.crop((left, top, right, bottom))

            # Resize to output size if different
            if cropped.width != self.output_size or cropped.height != self.output_size:
                cropped = cropped.resize(
                    (self.output_size, self.output_size),
                    Image.Resampling.LANCZOS
                )

            results.append((code, cropped))

        return results

    def split_from_file(self, file_path: str) -> List[Tuple[str, Image.Image]]:
        """
        Split a grid image file into individual expression images.

        Args:
            file_path: Path to the grid image file

        Returns:
            List of (expression_code, cropped_image) tuples
        """
        with Image.open(file_path) as img:
            # Convert to RGB if necessary (e.g., for PNG with alpha)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            return self.split(img)
