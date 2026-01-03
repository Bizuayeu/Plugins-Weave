"""HTML builder for expression UI."""

import json
from pathlib import Path
from typing import Dict


class HtmlBuilder:
    """Builds the final HTML from template and expression data."""

    PLACEHOLDER = "__IMAGES_PLACEHOLDER__"

    def __init__(self, template_path: str):
        """
        Initialize the HTML builder.

        Args:
            template_path: Path to the HTML template file

        Raises:
            FileNotFoundError: If template file does not exist
        """
        if not Path(template_path).exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        self.template_path = template_path
        self._template: str = ""

    def load_template(self) -> str:
        """
        Load the HTML template from file.

        Returns:
            The template content as a string

        Raises:
            ValueError: If template does not contain the placeholder
        """
        with open(self.template_path, "r", encoding="utf-8") as f:
            self._template = f.read()

        if self.PLACEHOLDER not in self._template:
            raise ValueError(f"Template is missing placeholder: {self.PLACEHOLDER}")

        return self._template

    def build(self, images_dict: Dict[str, str]) -> str:
        """
        Build the final HTML by replacing the placeholder with image data.

        Args:
            images_dict: Dictionary mapping expression codes to data URIs

        Returns:
            The complete HTML content
        """
        if not self._template:
            self.load_template()

        # Use json.dumps for proper serialization with escaping
        # This handles special characters correctly (quotes, backslashes, etc.)
        images_json = json.dumps(images_dict, ensure_ascii=False)
        # Template has: const IMAGES={__IMAGES_PLACEHOLDER__}
        # json.dumps returns {"key":"value"}, extract inner part (without braces)
        images_content = images_json[1:-1]  # Strip outer { }

        # Replace placeholder
        html = self._template.replace(self.PLACEHOLDER, images_content)

        return html

    def build_from_json(self, json_path: str) -> str:
        """
        Build HTML from a JSON file containing expression data.

        Args:
            json_path: Path to the JSON file

        Returns:
            The complete HTML content
        """
        with open(json_path, "r", encoding="utf-8") as f:
            images_dict = json.load(f)
        return self.build(images_dict)
