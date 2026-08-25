"""File reading operations."""

from __future__ import annotations

from pathlib import Path

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
        with Path(path).open(encoding=encoding) as f:
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
    except FileNotFoundError as e:
        raise SourceError(f"File not found: {path}") from e
    except PermissionError as e:
        raise SourceError(f"Permission denied: {path}") from e
    except UnicodeDecodeError as e:
        raise SourceError(f"Encoding error reading {path}: {e}") from e


def get_file_info(path: str) -> tuple[int, str]:
    """Get file size and extension.

    Returns:
        (size_in_bytes, extension_with_dot)

    Raises:
        SourceError: If file cannot be accessed.
    """
    try:
        size = Path(path).stat().st_size
        ext = Path(path).suffix
        return size, ext.lower()
    except OSError as e:
        raise SourceError(f"Cannot access file {path}: {e}") from e
