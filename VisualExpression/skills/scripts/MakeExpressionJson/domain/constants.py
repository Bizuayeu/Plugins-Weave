"""Expression code definitions and constants."""

from enum import Enum, auto


class ExpressionCategory(Enum):
    """Expression category definitions."""

    BASIC = auto()
    EMOTION = auto()
    NEGATIVE = auto()
    ANXIETY = auto()
    SPECIAL = auto()


# Grid configuration: 4 rows x 5 columns
GRID_ROWS = 4
GRID_COLS = 5
CELL_SIZE = 280  # pixels

# Number of Special category codes
SPECIAL_CODES_COUNT = 4

# Expression codes in grid order (left-to-right, top-to-bottom)
# Grid layout: 4 rows × 5 columns, each column = 1 category
#   Col1(Basic)  Col2(Emotion)  Col3(Negative)  Col4(Anxiety)  Col5(Special)
EXPRESSION_CODES: list[str] = [
    # Row1: Basic → Emotion → Negative → Anxiety → Special
    "normal", "joy", "anger", "anxiety", "sleepy",
    # Row2
    "smile", "elation", "sadness", "fear", "cynical",
    # Row3
    "focus", "surprise", "rage", "upset", "defeated",
    # Row4
    "diverge", "calm", "disgust", "worry", "dreamy",
]

# Japanese labels for each expression
EXPRESSION_LABELS: dict[str, str] = {
    "normal": "通常",
    "smile": "笑顔",
    "focus": "思考集中",
    "diverge": "思考発散",
    "joy": "喜び",
    "elation": "高揚",
    "surprise": "驚き",
    "calm": "平穏",
    "anger": "怒り",
    "sadness": "悲しみ",
    "rage": "激怒",
    "disgust": "嫌悪",
    "anxiety": "不安",
    "fear": "恐れ",
    "upset": "動揺",
    "worry": "心配",
    "sleepy": "うとうと",
    "cynical": "暗黒微笑",
    "defeated": "ぎゃふん",
    "dreamy": "ぽやぽや",
}

# Category codes using Enum keys
CATEGORY_CODES: dict[ExpressionCategory, list[str]] = {
    ExpressionCategory.BASIC: ["normal", "smile", "focus", "diverge"],
    ExpressionCategory.EMOTION: ["joy", "elation", "surprise", "calm"],
    ExpressionCategory.NEGATIVE: ["anger", "sadness", "rage", "disgust"],
    ExpressionCategory.ANXIETY: ["anxiety", "fear", "upset", "worry"],
    ExpressionCategory.SPECIAL: ["sleepy", "cynical", "defeated", "dreamy"],
}

# Grid configuration as a named tuple-like structure
GRID_CONFIG: dict[str, int] = {
    "rows": GRID_ROWS,
    "cols": GRID_COLS,
    "cell_size": CELL_SIZE,
    "total_width": GRID_COLS * CELL_SIZE,  # 1400px
    "total_height": GRID_ROWS * CELL_SIZE,  # 1120px
}


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
    return get_cell_position_dynamic(index, GRID_COLS, CELL_SIZE, CELL_SIZE)


# Default Special codes
DEFAULT_SPECIAL_CODES = ["sleepy", "cynical", "defeated", "dreamy"]
DEFAULT_SPECIAL_LABELS = {
    "sleepy": "うとうと",
    "cynical": "暗黒微笑",
    "defeated": "ぎゃふん",
    "dreamy": "ぽやぽや",
}


def build_expression_codes(special_codes: list[str] | None = None) -> list[str]:
    """
    Build expression codes list with optional custom Special codes.

    Args:
        special_codes: Custom Special codes (4 items). None = use defaults.

    Returns:
        List of 20 expression codes
    """
    if special_codes is None:
        special_codes = DEFAULT_SPECIAL_CODES

    if len(special_codes) != SPECIAL_CODES_COUNT:
        raise ValueError(
            f"Special codes must have exactly {SPECIAL_CODES_COUNT} items, "
            f"got {len(special_codes)}"
        )

    # Base codes (16) + Special (4) = 20
    # Grid order: left-to-right, top-to-bottom with Col = Category
    base_codes = [
        # Row1: Basic → Emotion → Negative → Anxiety
        "normal", "joy", "anger", "anxiety",
        # Row2
        "smile", "elation", "sadness", "fear",
        # Row3
        "focus", "surprise", "rage", "upset",
        # Row4
        "diverge", "calm", "disgust", "worry",
    ]
    # Insert Special codes at positions 4, 9, 14, 19 (Col5 for each row)
    result = []
    for i, code in enumerate(base_codes):
        result.append(code)
        if (i + 1) % 4 == 0:  # After each row's 4 base codes
            result.append(special_codes[(i + 1) // 4 - 1])
    return result


def build_expression_labels(special_codes: list[str] | None = None, special_labels: dict[str, str] | None = None) -> dict[str, str]:
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

    # Base labels (16)
    labels = {
        "normal": "通常",
        "smile": "笑顔",
        "focus": "思考集中",
        "diverge": "思考発散",
        "joy": "喜び",
        "elation": "高揚",
        "surprise": "驚き",
        "calm": "平穏",
        "anger": "怒り",
        "sadness": "悲しみ",
        "rage": "激怒",
        "disgust": "嫌悪",
        "anxiety": "不安",
        "fear": "恐れ",
        "upset": "動揺",
        "worry": "心配",
    }

    # Add Special labels
    for code in special_codes:
        if special_labels and code in special_labels:
            labels[code] = special_labels[code]
        else:
            labels[code] = code  # Use code as label if no translation

    return labels
