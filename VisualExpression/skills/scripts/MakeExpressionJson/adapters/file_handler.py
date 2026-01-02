"""File I/O operations for MakeExpressionJson."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class FileHandler:
    """Handles file operations for the expression system."""

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the file handler.

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
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir

    def write_json(
        self,
        data: Dict[str, Any],
        filename: str = "ExpressionImages.json",
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
        filename: str = "VisualExpressionUI.html",
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
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_skills_dir(self) -> Path:
        """
        Get the skills directory (parent of scripts).

        Returns:
            Path to the skills directory
        """
        # This file is in: skills/scripts/MakeExpressionJson/adapters/
        # Skills dir is: skills/
        return Path(__file__).parent.parent.parent.parent

    def get_default_template_path(self) -> Path:
        """
        Get the default template path.

        Returns:
            Path to VisualExpressionUI.template.html
        """
        return self.get_skills_dir() / "VisualExpressionUI.template.html"
