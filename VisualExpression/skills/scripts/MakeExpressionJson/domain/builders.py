"""Builder functions for expression codes and grid positions."""

from domain.definitions import (
    BASE_EXPRESSION_CODES,
    BASE_EXPRESSION_LABELS,
    DEFAULT_SPECIAL_CODES,
    DEFAULT_SPECIAL_LABELS,
    GRID_CONFIG,
    SPECIAL_CODES_COUNT,
)


def get_cell_position_dynamic(
    index: int, cols: int, cell_width: int, cell_height: int
) -> tuple[int, int, int, int]:
    """
    Get the pixel coordinates for a cell at the given index with dynamic parameters.

    Args:
        index: Cell index (0-based, left-to-right, top-to-bottom)
        cols: Number of columns in the grid
        cell_width: Width of each cell in pixels
        cell_height: Height of each cell in pixels

    Returns:
        Tuple of (left, top, right, bottom) pixel coordinates
    """
    row = index // cols
    col = index % cols

    left = col * cell_width
    top = row * cell_height

    return (left, top, left + cell_width, top + cell_height)


def get_cell_position(index: int) -> tuple[int, int, int, int]:
    """
    Get the pixel coordinates for a cell at the given index.

    Args:
        index: Cell index (0-19, left-to-right, top-to-bottom)

    Returns:
        Tuple of (left, top, right, bottom) pixel coordinates
    """
    cols = GRID_CONFIG["cols"]
    cell_size = GRID_CONFIG["cell_size"]
    return get_cell_position_dynamic(index, cols, cell_size, cell_size)


def build_expression_codes(special_codes: list[str] | None = None) -> list[str]:
    """
    Build expression codes list with optional custom Special codes.

    Args:
        special_codes: Custom Special codes (4 items). None = use defaults.

    Returns:
        List of 20 expression codes

    Raises:
        ValueError: If special_codes count is not 4, contains empty strings,
                    has duplicates, or overlaps with Base codes.
    """
    if special_codes is None:
        special_codes = DEFAULT_SPECIAL_CODES

    # Count validation (existing)
    if len(special_codes) != SPECIAL_CODES_COUNT:
        raise ValueError(
            f"Special codes must have exactly {SPECIAL_CODES_COUNT} items, got {len(special_codes)}"
        )

    # Empty string validation (new)
    if any(not code.strip() for code in special_codes):
        raise ValueError("Special codes cannot contain empty strings")

    # Duplicate validation (new)
    seen: set[str] = set()
    duplicates: list[str] = []
    for code in special_codes:
        if code in seen:
            duplicates.append(code)
        seen.add(code)
    if duplicates:
        raise ValueError(
            f"Special codes must be unique, found duplicates: {', '.join(set(duplicates))}"
        )

    # Base code overlap validation (new)
    base_set = set(BASE_EXPRESSION_CODES)
    overlaps = [code for code in special_codes if code in base_set]
    if overlaps:
        raise ValueError(f"Special codes cannot overlap with Base codes: {', '.join(overlaps)}")

    # Insert Special codes at positions 4, 9, 14, 19 (Col5 for each row)
    result = []
    for i, code in enumerate(BASE_EXPRESSION_CODES):
        result.append(code)
        if (i + 1) % 4 == 0:  # After each row's 4 base codes
            result.append(special_codes[(i + 1) // 4 - 1])
    return result


def build_expression_labels(
    special_codes: list[str] | None = None,
    special_labels: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Build expression labels dict with optional custom Special labels.

    Args:
        special_codes: Custom Special codes (4 items). None = use defaults.
        special_labels: Custom labels for Special codes. None = use code as label.

    Returns:
        Dict mapping codes to Japanese labels
    """
    if special_codes is None:
        special_codes = DEFAULT_SPECIAL_CODES
        special_labels = DEFAULT_SPECIAL_LABELS

    # Base labels (16) - use copy to avoid mutating the shared constant
    labels = BASE_EXPRESSION_LABELS.copy()

    # Add Special labels
    for code in special_codes:
        if special_labels and code in special_labels:
            labels[code] = special_labels[code]
        else:
            labels[code] = code  # Use code as label if no translation

    return labels
