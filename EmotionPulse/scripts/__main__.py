"""Entry point: python -m scripts statusline."""

from __future__ import annotations

import io
import sys


def _ensure_utf8() -> None:
    """Ensure stdout/stderr use UTF-8 encoding."""
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main() -> None:
    """Dispatch to statusline mode."""
    _ensure_utf8()
    from scripts.interfaces.statusline import run_statusline

    run_statusline()


if __name__ == "__main__":
    main()
