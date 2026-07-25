"""Statusline script: read emotion state and output emoji string."""

from __future__ import annotations

from scripts.application.formatter import format_emotion_display
from scripts.application.state_manager import load_state
from scripts.infrastructure.config_loader import load_display_config


def run_statusline() -> None:
    """Read emotion_state.json and print formatted emoji string to stdout.

    Designed to be fast (< 100ms). No API calls. Outputs empty string on any error.
    """
    try:
        vector = load_state()
        if vector is None:
            return

        config = load_display_config()
        output = format_emotion_display(vector, config)
        if output:
            print(output)
    except Exception:
        pass  # Never fail, never delay


if __name__ == "__main__":
    run_statusline()
