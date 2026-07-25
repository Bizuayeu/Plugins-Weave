"""CLI: receive emotion JSON argument, validate, and write emotion_state.json."""

from __future__ import annotations

import json
import sys

from scripts.application.state_manager import save_state
from scripts.domain.models import EmotionVector


def main() -> None:
    """Parse emotion scores from CLI argument and save to state file.

    Usage: python emotion_writer.py '{"calm":2,"curiosity":3,...}'
    """
    if len(sys.argv) < 2:
        print("Usage: emotion_writer.py '<json scores>'", file=sys.stderr)
        sys.exit(1)

    try:
        scores = json.loads(sys.argv[1])
    except (json.JSONDecodeError, ValueError) as e:
        print(f"EmotionPulse: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(scores, dict):
        print(f"EmotionPulse: Expected dict, got {type(scores).__name__}", file=sys.stderr)
        sys.exit(1)

    vector = EmotionVector.from_raw_scores(scores)
    save_state(vector)


if __name__ == "__main__":
    main()
