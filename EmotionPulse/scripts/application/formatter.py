"""Format EmotionVector as emoji string for statusline display."""
from __future__ import annotations

from scripts.domain.constants import (
    EMOTION_INDICATORS,
    EMOTION_KEYS,
    EMOTION_LABELS_EN,
    EMOTION_LABELS_JA,
)
from scripts.domain.models import DisplayConfig, EmotionVector


def format_emotion_display(
    vector: EmotionVector,
    config: DisplayConfig | None = None,
) -> str:
    """Format EmotionVector as statusline string.

    Args:
        vector: The emotion vector to display.
        config: Display configuration (labels, language). Defaults used if None.

    Returns:
        Formatted string like "安定性:🔵🔵, 知的興奮:🟢🟢🟢, 遊び心:🟡"
        or "🔵🔵, 🟢🟢🟢, 🟡" if labels are off.
    """
    if config is None:
        config = DisplayConfig()

    labels = EMOTION_LABELS_JA if config.language == "ja" else EMOTION_LABELS_EN

    parts: list[str] = []
    for key in EMOTION_KEYS:
        value = vector.emotions.get(key, 0)
        if value <= 0:
            continue
        indicator = EMOTION_INDICATORS[key]
        icons = indicator * value
        if config.show_labels:
            parts.append(f"{labels[key]}:{icons}")
        else:
            parts.append(icons)

    return ", ".join(parts)
