"""Generate Stop hook configuration for settings.json."""

from __future__ import annotations

import os

from scripts.domain.constants import STOP_SYSTEM_MESSAGE
from scripts.infrastructure.path_resolver import get_plugin_root

_DEV_FALLBACK = os.path.expanduser("~/DEV/plugins-weave/EmotionPulse")


def _resolve_plugin_base() -> str:
    """Return plugin root as string, falling back to DEV candidate."""
    root = get_plugin_root()
    return str(root) if root is not None else _DEV_FALLBACK


def _handler_path() -> str:
    """Resolve absolute path to hooks/stop_handler.py for settings.json."""
    base = _resolve_plugin_base()
    return os.path.join(base, "hooks", "stop_handler.py").replace("\\", "/")


def get_launcher_path() -> str:
    """Resolve the absolute path to hooks/emotion_writer_launcher.py.

    The launcher manages sys.path so emotion_writer loads regardless of
    caller's cwd (avoiding collision with other plugins' scripts/ packages).
    """
    base = _resolve_plugin_base()
    return os.path.join(base, "hooks", "emotion_writer_launcher.py").replace("\\", "/")


def build_system_message() -> str:
    """Build the systemMessage with resolved launcher path."""
    return STOP_SYSTEM_MESSAGE.format(launcher_path=get_launcher_path())


def build_stop_hook_entry() -> dict[str, object]:
    """Build a Stop hook config entry for settings.json (command type)."""
    return {
        "hooks": [
            {
                "type": "command",
                "command": f'python "{_handler_path()}"',
                "timeout": 5000,
            }
        ],
    }
