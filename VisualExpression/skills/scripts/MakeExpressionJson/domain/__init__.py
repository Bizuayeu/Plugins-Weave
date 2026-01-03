"""Domain layer for MakeExpressionJson."""

# Re-export from definitions (data)
# Re-export from builders (functions)
from .builders import (
    build_expression_codes,
    build_expression_labels,
    get_cell_position,
    get_cell_position_dynamic,
)
from .definitions import (
    CATEGORY_CODES,
    CELL_SIZE,
    DEFAULT_SPECIAL_CODES,
    DEFAULT_SPECIAL_LABELS,
    EXPRESSION_CODES,
    EXPRESSION_LABELS,
    GRID_COLS,
    GRID_CONFIG,
    GRID_ROWS,
    SPECIAL_CODES_COUNT,
    ExpressionCategory,
)

# Re-export from grid_layout
from .grid_layout import GridLayout

# Re-export from models
# Note: GridConfig has been removed and merged into GridLayout
from .models import ExpressionImage

__all__ = [
    "CATEGORY_CODES",
    "CELL_SIZE",
    "DEFAULT_SPECIAL_CODES",
    "DEFAULT_SPECIAL_LABELS",
    "EXPRESSION_CODES",
    "EXPRESSION_LABELS",
    "GRID_COLS",
    "GRID_CONFIG",
    "GRID_ROWS",
    "SPECIAL_CODES_COUNT",
    "ExpressionCategory",
    "ExpressionImage",
    # GridConfig removed - use GridLayout instead
    "GridLayout",
    "build_expression_codes",
    "build_expression_labels",
    "get_cell_position",
    "get_cell_position_dynamic",
]
