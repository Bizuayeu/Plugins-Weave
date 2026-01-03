"""Grid dimension validation functions.

Shared validation logic for grid-based image operations.
Extracted from image_splitter.py and grid_layout.py to maintain DRY principle.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image


def validate_grid_dimensions(
    width: int,
    height: int,
    cols: int,
    rows: int,
    cell_size: int | None = None,
) -> tuple[bool, str]:
    """
    Validate that dimensions are compatible with a grid layout.

    Args:
        width: Image/container width in pixels
        height: Image/container height in pixels
        cols: Number of columns in the grid
        rows: Number of rows in the grid
        cell_size: Optional cell size for recommendation in error message

    Returns:
        Tuple of (is_valid, error_message).
        If valid, returns (True, "").
        If invalid, returns (False, descriptive error message).
    """
    if width % cols != 0:
        if cell_size is not None:
            expected = cols * cell_size
            return (
                False,
                f"Image width {width}px is not divisible by {cols} columns. "
                f"Recommended: {expected}px (= {cols} x {cell_size}px/cell)",
            )
        return (
            False,
            f"Image width {width}px is not divisible by {cols} columns.",
        )

    if height % rows != 0:
        if cell_size is not None:
            expected = rows * cell_size
            return (
                False,
                f"Image height {height}px is not divisible by {rows} rows. "
                f"Recommended: {expected}px (= {rows} x {cell_size}px/cell)",
            )
        return (
            False,
            f"Image height {height}px is not divisible by {rows} rows.",
        )

    return (True, "")


def validate_image_dimensions(
    image: "Image.Image",
    cols: int,
    rows: int,
    cell_size: int | None = None,
) -> tuple[bool, str]:
    """
    Validate that a PIL Image has dimensions compatible with a grid layout.

    This is a convenience wrapper around validate_grid_dimensions that
    extracts width and height from a PIL Image object.

    Args:
        image: PIL Image object
        cols: Number of columns in the grid
        rows: Number of rows in the grid
        cell_size: Optional cell size for recommendation in error message

    Returns:
        Tuple of (is_valid, error_message).
        If valid, returns (True, "").
        If invalid, returns (False, descriptive error message).
    """
    return validate_grid_dimensions(
        width=image.width,
        height=image.height,
        cols=cols,
        rows=rows,
        cell_size=cell_size,
    )
