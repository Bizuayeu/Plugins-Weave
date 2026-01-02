"""Expression code definitions and constants."""

from typing import Dict, List, Tuple

# Grid configuration: 4 rows x 5 columns
GRID_ROWS = 4
GRID_COLS = 5
CELL_SIZE = 280  # pixels

# Expression codes in grid order (left-to-right, top-to-bottom)
EXPRESSION_CODES: List[str] = [
    # Row 1: Basic
    "normal", "smile", "focus", "diverge",
    # Row 2: Emotion
    "joy", "elation", "surprise", "calm",
    # Row 3: Negative
    "anger", "sadness", "rage", "disgust",
    # Row 4: Anxiety
    "anxiety", "fear", "upset", "worry",
    # Row 5: Special
    "sleepy", "cynical", "defeated", "dreamy",
]

# Japanese labels for each expression
EXPRESSION_LABELS: Dict[str, str] = {
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

# Category definitions
CATEGORIES: Dict[str, List[str]] = {
    "Basic": ["normal", "smile", "focus", "diverge"],
    "Emotion": ["joy", "elation", "surprise", "calm"],
    "Negative": ["anger", "sadness", "rage", "disgust"],
    "Anxiety": ["anxiety", "fear", "upset", "worry"],
    "Special": ["sleepy", "cynical", "defeated", "dreamy"],
}

# Grid configuration as a named tuple-like structure
GRID_CONFIG: Dict[str, int] = {
    "rows": GRID_ROWS,
    "cols": GRID_COLS,
    "cell_size": CELL_SIZE,
    "total_width": GRID_COLS * CELL_SIZE,  # 1400px
    "total_height": GRID_ROWS * CELL_SIZE,  # 1120px
}


def get_cell_position(index: int) -> Tuple[int, int, int, int]:
    """
    Get the pixel coordinates for a cell at the given index.

    Args:
        index: Cell index (0-19, left-to-right, top-to-bottom)

    Returns:
        Tuple of (left, top, right, bottom) pixel coordinates
    """
    row = index // GRID_COLS
    col = index % GRID_COLS

    left = col * CELL_SIZE
    top = row * CELL_SIZE
    right = left + CELL_SIZE
    bottom = top + CELL_SIZE

    return (left, top, right, bottom)


# Default Special codes
DEFAULT_SPECIAL_CODES = ["sleepy", "cynical", "defeated", "dreamy"]
DEFAULT_SPECIAL_LABELS = {
    "sleepy": "うとうと",
    "cynical": "暗黒微笑",
    "defeated": "ぎゃふん",
    "dreamy": "ぽやぽや",
}


def build_expression_codes(special_codes: List[str] = None) -> List[str]:
    """
    Build expression codes list with optional custom Special codes.

    Args:
        special_codes: Custom Special codes (4 items). None = use defaults.

    Returns:
        List of 20 expression codes
    """
    if special_codes is None:
        special_codes = DEFAULT_SPECIAL_CODES

    if len(special_codes) != 4:
        raise ValueError(f"Special codes must have exactly 4 items, got {len(special_codes)}")

    # Base codes (16) + Special (4) = 20
    base_codes = [
        "normal", "smile", "focus", "diverge",
        "joy", "elation", "surprise", "calm",
        "anger", "sadness", "rage", "disgust",
        "anxiety", "fear", "upset", "worry",
    ]
    return base_codes + list(special_codes)


def build_expression_labels(special_codes: List[str] = None, special_labels: Dict[str, str] = None) -> Dict[str, str]:
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
