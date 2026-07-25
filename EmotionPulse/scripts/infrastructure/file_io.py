"""Low-level file operations: atomic write, safe JSON read."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path


def write_json_atomic(path: Path, data: Mapping[str, object]) -> None:
    """Write JSON atomically via tmp file + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".emotion_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, str(path))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise


def read_json_safe(path: Path) -> dict[str, object] | None:
    """Read JSON file, return None on any error."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data  # type: ignore[return-value]
        return None
    except (OSError, json.JSONDecodeError, ValueError):
        return None
