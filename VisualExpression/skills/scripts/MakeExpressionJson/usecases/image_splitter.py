"""Image splitting logic for expression grids."""

from PIL import Image

from domain import (
    GRID_CONFIG,
    build_expression_codes,
    get_cell_position_dynamic,
)
from domain.validators import validate_image_dimensions


class ImageSplitter:
    """Splits a grid image into individual expression images."""

    def __init__(
        self,
        rows: int | None = None,
        cols: int | None = None,
        output_size: int | None = None,
        special_codes: list[str] | None = None,
        offsets: dict[str, dict[str, int]] | None = None,
    ):
        """
        Initialize the image splitter.

        Args:
            rows: Number of rows in the grid (default: from GRID_CONFIG)
            cols: Number of columns in the grid (default: from GRID_CONFIG)
            output_size: Output size for each cropped image (default: from GRID_CONFIG)
            special_codes: Custom Special category codes (4 items). None = use defaults.
            offsets: Per-expression crop offsets. Format: {"code": {"x": int, "y": int}}.
                     Positive x = right, Positive y = down.

        Note:
            Cell size is automatically calculated from image dimensions.
        """
        # Use GRID_CONFIG as defaults if not provided
        if rows is None:
            rows = GRID_CONFIG["rows"]
        if cols is None:
            cols = GRID_CONFIG["cols"]
        if output_size is None:
            output_size = GRID_CONFIG["cell_size"]
        self.rows = rows
        self.cols = cols
        self.output_size = output_size
        self.expression_codes = build_expression_codes(special_codes)
        self.offsets = offsets or {}

    def validate_image(self, image: Image.Image) -> tuple[bool, str]:
        """
        Validate that the image can be split into the expected grid.

        Args:
            image: PIL Image object

        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_image_dimensions(
            image=image,
            cols=self.cols,
            rows=self.rows,
            cell_size=self.output_size,
        )

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

            # Center crop or resize to output size
            if cropped.width > self.output_size and cropped.height > self.output_size:
                # Center crop: extract center portion (absorbs positioning errors)
                margin_x = (cropped.width - self.output_size) // 2
                margin_y = (cropped.height - self.output_size) // 2

                # Apply per-expression offset if specified
                if code in self.offsets:
                    offset = self.offsets[code]
                    margin_x += offset.get("x", 0)
                    margin_y += offset.get("y", 0)

                cropped = cropped.crop(
                    (
                        margin_x,
                        margin_y,
                        margin_x + self.output_size,
                        margin_y + self.output_size,
                    )
                )
            elif cropped.width != self.output_size or cropped.height != self.output_size:
                # Fallback: resize for smaller cells
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
                rgb_img = img.convert("RGB")
                return self.split(rgb_img)
            return self.split(img)
