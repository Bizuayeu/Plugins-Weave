"""Image splitting logic for expression grids."""

from PIL import Image

from domain import (
    CELL_SIZE,
    GRID_COLS,
    GRID_ROWS,
    build_expression_codes,
    get_cell_position_dynamic,
)


class ImageSplitter:
    """Splits a grid image into individual expression images."""

    def __init__(
        self,
        rows: int = GRID_ROWS,
        cols: int = GRID_COLS,
        output_size: int = CELL_SIZE,
        special_codes: list[str] | None = None,
    ):
        """
        Initialize the image splitter.

        Args:
            rows: Number of rows in the grid (default: 4)
            cols: Number of columns in the grid (default: 5)
            output_size: Output size for each cropped image (default: 280)
            special_codes: Custom Special category codes (4 items). None = use defaults.

        Note:
            Cell size is automatically calculated from image dimensions.
        """
        self.rows = rows
        self.cols = cols
        self.output_size = output_size
        self.expression_codes = build_expression_codes(special_codes)

    def validate_image(self, image: Image.Image) -> tuple[bool, str]:
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

    def split(self, image: Image.Image) -> list[tuple[str, Image.Image]]:
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

        results: list[tuple[str, Image.Image]] = []

        for i, code in enumerate(self.expression_codes):
            left, top, right, bottom = get_cell_position_dynamic(
                i, self.cols, cell_width, cell_height
            )
            cropped = image.crop((left, top, right, bottom))

            # Resize to output size if different
            if cropped.width != self.output_size or cropped.height != self.output_size:
                cropped = cropped.resize(
                    (self.output_size, self.output_size), Image.Resampling.LANCZOS
                )

            results.append((code, cropped))

        return results

    def split_from_file(self, file_path: str) -> list[tuple[str, Image.Image]]:
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
