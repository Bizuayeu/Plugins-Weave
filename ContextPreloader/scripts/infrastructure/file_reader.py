"""File reading operations."""
from __future__ import annotations

import os

from scripts.domain.exceptions import SourceError


def read_text_file(path: str, encoding: str, max_lines: int) -> str:
    """Read a text file and return its content.

    Args:
        path: File path to read.
        encoding: Text encoding (e.g. 'utf-8').
        max_lines: Max lines to read. 0 = unlimited.

    Returns:
        File content as string.

    Raises:
        SourceError: If file cannot be read.
    """
    try:
        with open(path, "r", encoding=encoding) as f:
            if max_lines > 0:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append("[... truncated]")
                        break
                    lines.append(line.rstrip("\n"))
                return "\n".join(lines)
            else:
                return f.read()
    except FileNotFoundError:
        raise SourceError(f"File not found: {path}")
    except PermissionError:
        raise SourceError(f"Permission denied: {path}")
    except UnicodeDecodeError as e:
        raise SourceError(f"Encoding error reading {path}: {e}")


def get_file_info(path: str) -> tuple[int, str]:
    """Get file size and extension.

    Returns:
        (size_in_bytes, extension_with_dot)

    Raises:
        SourceError: If file cannot be accessed.
    """
    try:
        size = os.path.getsize(path)
        _, ext = os.path.splitext(path)
        return size, ext.lower()
    except OSError as e:
        raise SourceError(f"Cannot access file {path}: {e}")
