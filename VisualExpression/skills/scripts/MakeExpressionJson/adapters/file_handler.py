"""File I/O operations for MakeExpressionJson."""

import json
import os
from pathlib import Path
from typing import Any

from .file_constants import (
    DEFAULT_HTML_FILENAME,
    DEFAULT_JSON_FILENAME,
    DEFAULT_TEMPLATE_FILENAME,
    SKILLS_DIR_ENV_VAR,
    SKILLS_DIR_MARKERS,
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


class FileHandler:
    """Handles file operations for the expression system."""

    def __init__(self, output_dir: str | None = None, skills_dir: str | None = None):
        """
        Initialize the file handler.

        Args:
            output_dir: Default output directory (creates if not exists)
            skills_dir: Explicit skills directory path (overrides auto-detection)
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self._skills_dir = Path(skills_dir) if skills_dir else None

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

    def get_skills_dir(self) -> Path:
        """
        Get the skills directory.

        Priority order:
        1. Explicit skills_dir parameter (constructor)
        2. VISUAL_EXPRESSION_SKILLS_DIR environment variable
        3. Upward search for marker files (SKILL.md or template)
        4. Relative path calculation (fallback)

        Returns:
            Path to the skills directory
        """
        # 1. Use explicit path if provided (highest priority)
        if self._skills_dir:
            return self._skills_dir

        # 2. Check environment variable
        env_dir = os.environ.get(SKILLS_DIR_ENV_VAR)
        if env_dir:
            path = Path(env_dir)
            if path.exists():
                return path

        # 3. Search upward for marker files
        current = Path(__file__).parent
        markers = SKILLS_DIR_MARKERS

        for _ in range(10):  # Limit search depth
            for marker in markers:
                if (current / marker).exists():
                    return current
            if current.parent == current:
                break
            current = current.parent

        # 4. Fallback: use relative path calculation (original behavior)
        # This file is in: skills/scripts/MakeExpressionJson/adapters/
        # Skills dir is: skills/
        return Path(__file__).parent.parent.parent.parent

    def get_default_template_path(self) -> Path:
        """
        Get the default template path.

        Returns:
            Path to VisualExpressionUI.template.html
        """
        return self.get_skills_dir() / DEFAULT_TEMPLATE_FILENAME
