"""Expression code definitions and constants (data only)."""

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
# Grid layout: 4 rows x 5 columns, each column = 1 category
#   Col1(Basic)  Col2(Emotion)  Col3(Negative)  Col4(Anxiety)  Col5(Special)
EXPRESSION_CODES: list[str] = [
    # Row1: Basic -> Emotion -> Negative -> Anxiety -> Special
    "normal",
    "joy",
    "anger",
    "anxiety",
    "sleepy",
    # Row2
    "smile",
    "elation",
    "sadness",
    "fear",
    "cynical",
    # Row3
    "focus",
    "surprise",
    "rage",
    "upset",
    "defeated",
    # Row4
    "diverge",
    "calm",
    "disgust",
    "worry",
    "dreamy",
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

# Default Special codes
DEFAULT_SPECIAL_CODES = ["sleepy", "cynical", "defeated", "dreamy"]
DEFAULT_SPECIAL_LABELS = {
    "sleepy": "うとうと",
    "cynical": "暗黒微笑",
    "defeated": "ぎゃふん",
    "dreamy": "ぽやぽや",
}
