"""Pure detection functions (no I/O)."""
from __future__ import annotations

import os

from .constants import FILE_TYPE_LABELS


def is_url(path: str) -> bool:
    """Check if a path string is a URL."""
    return path.startswith("http://") or path.startswith("https://")


def detect_source_kind(
    path: str, text_extensions: list[str], forced_type: str
) -> str:
    """Detect how a source should be handled.

    Returns: "text" | "binary" | "url"
    """
    if is_url(path):
        if forced_type == "binary":
            return "binary"
        return "url"

    if forced_type == "text":
        return "text"
    if forced_type == "binary":
        return "binary"

    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext in text_extensions:
        return "text"
    return "binary"


def format_file_size(size_bytes: int) -> str:
    """Format byte count to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_file_type_label(ext: str) -> str:
    """Get human-readable file type label from extension."""
    ext = ext.lower()
    if ext in FILE_TYPE_LABELS:
        return FILE_TYPE_LABELS[ext]
    return f"{ext.lstrip('.').upper()} file"
