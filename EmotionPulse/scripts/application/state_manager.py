"""Manage emotion_state.json persistence."""

from __future__ import annotations

from pathlib import Path

from scripts.domain.models import EmotionVector
from scripts.infrastructure.file_io import read_json_safe, write_json_atomic
from scripts.infrastructure.path_resolver import get_state_file_path


def save_state(vector: EmotionVector, path: Path | None = None) -> None:
    """Save EmotionVector to JSON file atomically."""
    if path is None:
        path = get_state_file_path()
    write_json_atomic(path, vector.to_dict())


def load_state(path: Path | None = None) -> EmotionVector | None:
    """Load EmotionVector from JSON file, returning None on any failure."""
    if path is None:
        path = get_state_file_path()
    data = read_json_safe(path)
    if data is None:
        return None
    return EmotionVector.from_dict(data)
