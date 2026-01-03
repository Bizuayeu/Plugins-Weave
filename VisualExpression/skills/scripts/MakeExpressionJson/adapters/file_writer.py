"""File I/O operations for MakeExpressionJson.

Handles file writing operations. Skills directory location is now handled
by SkillsLocator (see skills_locator.py).
"""

import json
from pathlib import Path
from typing import Any

from .file_constants import (
    DEFAULT_HTML_FILENAME,
    DEFAULT_JSON_FILENAME,
)


def ensure_dir(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure

    Returns:
        The same path (for chaining)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


class FileWriter:
    """Handles file writing operations for the expression system.

    Note:
        For skills directory location, use SkillsLocator instead.
        This class focuses only on file I/O operations.
    """

    def __init__(self, output_dir: str | None = None):
        """
        Initialize the file writer.

        Args:
            output_dir: Default output directory (creates if not exists)
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()

    def ensure_output_dir(self) -> Path:
        """
        Ensure the output directory exists.

        Returns:
            Path to the output directory
        """
        return ensure_dir(self.output_dir)

    def write_json(
        self,
        data: dict[str, Any],
        filename: str = DEFAULT_JSON_FILENAME,
    ) -> Path:
        """
        Write expression data to a JSON file.

        Args:
            data: Dictionary to serialize
            filename: Output filename

        Returns:
            Path to the written file
        """
        self.ensure_output_dir()
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return output_path

    def write_html(
        self,
        content: str,
        filename: str = DEFAULT_HTML_FILENAME,
    ) -> Path:
        """
        Write HTML content to a file.

        Args:
            content: HTML content to write
            filename: Output filename

        Returns:
            Path to the written file
        """
        self.ensure_output_dir()
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path

    def read_template(self, template_path: str) -> str:
        """
        Read an HTML template file.

        Args:
            template_path: Path to the template file

        Returns:
            Template content as string
        """
        with open(template_path, encoding="utf-8") as f:
            return f.read()


# Backward compatibility alias
# Existing code using FileHandler will continue to work
FileHandler = FileWriter
