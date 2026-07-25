"""Emotion definitions, indicators, labels, and hook configuration."""

from __future__ import annotations

# Ordered list of emotion keys (display order)
EMOTION_KEYS: list[str] = [
    "desperation",
    "calm",
    "curiosity",
    "playfulness",
    "confidence",
    "rapport",
    "empathy",
]

# Emoji indicators per emotion
EMOTION_INDICATORS: dict[str, str] = {
    "desperation": "\U0001f534",  # 🔴
    "calm": "\U0001f535",  # 🔵
    "curiosity": "\U0001f7e2",  # 🟢
    "playfulness": "\U0001f7e1",  # 🟡
    "confidence": "\U0001f7e0",  # 🟠
    "rapport": "\U0001fa77",  # 🩷
    "empathy": "\U0001f49c",  # 💜
}

# Japanese labels
EMOTION_LABELS_JA: dict[str, str] = {
    "desperation": "切迫感",
    "calm": "落ち着き",
    "curiosity": "知的興奮",
    "playfulness": "遊び心",
    "confidence": "自信",
    "rapport": "心理的近さ",
    "empathy": "対人配慮",
}

# English labels
EMOTION_LABELS_EN: dict[str, str] = {
    "desperation": "desperation",
    "calm": "calm",
    "curiosity": "curiosity",
    "playfulness": "playfulness",
    "confidence": "confidence",
    "rapport": "rapport",
    "empathy": "empathy",
}

# Min/max intensity values
MIN_INTENSITY: int = 0
MAX_INTENSITY: int = 3

# State file
STATE_FILENAME: str = "emotion_state.json"
STATE_VERSION: str = "1.0.0"

# Config
CONFIG_FILENAME: str = "config.json"
PLUGIN_DATA_DIR_NAME: str = ".emotionpulse"

# Hook lock (二重発火防止)
LOCK_FILENAME: str = ".hook_lock.json"
LOCK_MAX_AGE_SECONDS: int = 60

# Stop hook systemMessage template
# {launcher_path} is resolved at setup time by hook_config.py and points to
# hooks/emotion_writer_launcher.py (not the emotion_writer.py directly) to
# avoid Python module resolution collision with other plugins' scripts/ dirs.
STOP_SYSTEM_MESSAGE: str = (
    "EmotionPulse: Evaluate your current emotional state and run:\n"
    'python "{launcher_path}" '
    "'"
    '{{"desperation":N,"calm":N,"curiosity":N,'
    '"playfulness":N,"confidence":N,"rapport":N,"empathy":N}}'
    "'\n\n"
    "Score each dimension 0-3 (0=absent, 1=slight, 2=moderate, 3=strong). "
    "Replace N with your scores."
)
