"""GridLayout dataclass for expression grid operations."""

from dataclasses import dataclass

from domain.builders import build_expression_codes
from domain.definitions import (
    EXPRESSION_CODES,
    GRID_CONFIG,
)


@dataclass(frozen=True)
class GridLayout:
    """
    Immutable representation of an expression grid layout.

    This dataclass encapsulates all grid-related calculations and provides
    a clean interface for working with expression grids.

    Attributes:
        rows: Number of rows in the grid
        cols: Number of columns in the grid
        cell_size: Size of each cell in pixels (square cells)
        expression_codes: Tuple of expression codes in grid order
    """

    rows: int
    cols: int
    cell_size: int
    expression_codes: tuple[str, ...]

    @classmethod
    def default(cls) -> "GridLayout":
        """
        Create a GridLayout with default settings.

        Returns:
            GridLayout with 4 rows, 5 cols, 280px cells, and default expressions
        """
        return cls(
            rows=GRID_CONFIG["rows"],
            cols=GRID_CONFIG["cols"],
            cell_size=GRID_CONFIG["cell_size"],
            expression_codes=tuple(EXPRESSION_CODES),
        )

    @classmethod
    def with_special_codes(cls, special_codes: list[str]) -> "GridLayout":
        """
        Create a GridLayout with custom special codes.

        Args:
            special_codes: List of 4 custom special expression codes

        Returns:
            GridLayout with custom special codes
        """
        codes = build_expression_codes(special_codes)
        return cls(
            rows=GRID_CONFIG["rows"],
            cols=GRID_CONFIG["cols"],
            cell_size=GRID_CONFIG["cell_size"],
            expression_codes=tuple(codes),
        )

    def get_cell_position(self, index: int) -> tuple[int, int, int, int]:
        """
        Get the pixel coordinates for a cell at the given index.

        Args:
            index: Cell index (0-based, left-to-right, top-to-bottom)

        Returns:
            Tuple of (left, top, right, bottom) pixel coordinates
        """
        row = index // self.cols
        col = index % self.cols

        left = col * self.cell_size
        top = row * self.cell_size

        return (left, top, left + self.cell_size, top + self.cell_size)

    def expression_at(self, row: int, col: int) -> str:
        """
        Get the expression code at a specific grid position.

        Args:
            row: Row index (0-based)
            col: Column index (0-based)

        Returns:
            Expression code at the specified position
        """
        index = row * self.cols + col
        return self.expression_codes[index]

    def validate_dimensions(self, width: int, height: int) -> tuple[bool, str]:
        """
        Validate that image dimensions are compatible with this grid.

        Args:
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Tuple of (is_valid, error_message)
        """
        if width % self.cols != 0:
            return (
                False,
                f"Image width {width}px is not divisible by {self.cols} columns. "
                f"Recommended: {self.expected_width}px",
            )
        if height % self.rows != 0:
            return (
                False,
                f"Image height {height}px is not divisible by {self.rows} rows. "
                f"Recommended: {self.expected_height}px",
            )

        return (True, "")

    @property
    def total_cells(self) -> int:
        """Total number of cells in the grid."""
        return self.rows * self.cols

    @property
    def expected_width(self) -> int:
        """Expected image width in pixels."""
        return self.cols * self.cell_size

    @property
    def expected_height(self) -> int:
        """Expected image height in pixels."""
        return self.rows * self.cell_size
