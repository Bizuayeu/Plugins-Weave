"""Generate Stop hook configuration for settings.json."""
from __future__ import annotations

import os

from scripts.domain.constants import STOP_SYSTEM_MESSAGE


def get_writer_path() -> str:
    """Resolve the absolute path to emotion_writer.py."""
    candidates = [
        os.path.expanduser("~/DEV/plugins-weave/EmotionPulse"),
        os.path.expanduser("~/.claude/plugins/marketplaces/plugins-weave/EmotionPulse"),
    ]
    for base in candidates:
        path = os.path.join(base, "scripts", "interfaces", "emotion_writer.py")
        if os.path.isfile(path):
            return path.replace("\\", "/")
    # Fallback to first candidate
    return os.path.join(candidates[0], "scripts", "interfaces", "emotion_writer.py").replace(
        "\\", "/"
    )


def build_system_message() -> str:
    """Build the systemMessage with resolved writer path."""
    return STOP_SYSTEM_MESSAGE.format(writer_path=get_writer_path())


def build_stop_hook_entry() -> dict[str, object]:
    """Build a Stop hook config entry for settings.json (command type)."""
    candidates = [
        os.path.expanduser("~/DEV/plugins-weave/EmotionPulse"),
        os.path.expanduser("~/.claude/plugins/marketplaces/plugins-weave/EmotionPulse"),
    ]
    handler_path = ""
    for base in candidates:
        path = os.path.join(base, "hooks", "stop_handler.py")
        if os.path.isfile(path):
            handler_path = path.replace("\\", "/")
            break
    if not handler_path:
        handler_path = os.path.join(
            candidates[0], "hooks", "stop_handler.py"
        ).replace("\\", "/")

    return {
        "hooks": [{
            "type": "command",
            "command": f'python "{handler_path}"',
            "timeout": 5000,
        }],
    }
