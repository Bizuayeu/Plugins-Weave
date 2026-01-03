"""Expression code definitions and constants (data only)."""

from enum import Enum, auto


class ExpressionCategory(Enum):
    """Expression category definitions."""

    BASIC = auto()
    EMOTION = auto()
    NEGATIVE = auto()
    ANXIETY = auto()
    SPECIAL = auto()


# Grid configuration (single source of truth)
GRID_CONFIG: dict[str, int] = {
    "rows": 4,
    "cols": 5,
    "cell_size": 280,
    "total_width": 1400,  # 5 * 280
    "total_height": 1120,  # 4 * 280
}

# Number of Special category codes
SPECIAL_CODES_COUNT = 4

# Base expression codes (16 codes, excluding Special category)
# Grid order: left-to-right, top-to-bottom, skipping Col5 (Special)
BASE_EXPRESSION_CODES: list[str] = [
    # Row1: Basic -> Emotion -> Negative -> Anxiety
    "normal",
    "joy",
    "anger",
    "anxiety",
    # Row2
    "smile",
    "elation",
    "sadness",
    "fear",
    # Row3
    "focus",
    "surprise",
    "rage",
    "upset",
    # Row4
    "diverge",
    "calm",
    "disgust",
    "worry",
]

# Base expression labels (16 labels, excluding Special category)
BASE_EXPRESSION_LABELS: dict[str, str] = {
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

# Default Special codes
DEFAULT_SPECIAL_CODES = ["sleepy", "cynical", "defeated", "dreamy"]
DEFAULT_SPECIAL_LABELS = {
    "sleepy": "うとうと",
    "cynical": "暗黒微笑",
    "defeated": "ぎゃふん",
    "dreamy": "ぽやぽや",
}
