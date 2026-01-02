"""HTML builder for expression UI."""

import json
from typing import Dict


class HtmlBuilder:
    """Builds the final HTML from template and expression data."""

    PLACEHOLDER = "__IMAGES_PLACEHOLDER__"

    def __init__(self, template_path: str):
        """
        Initialize the HTML builder.

        Args:
            template_path: Path to the HTML template file
        """
        self.template_path = template_path
        self._template: str = ""

    def load_template(self) -> str:
        """
        Load the HTML template from file.

        Returns:
            The template content as a string
        """
        with open(self.template_path, "r", encoding="utf-8") as f:
            self._template = f.read()
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

        # Build the JavaScript object string
        # Format: key:'value',key:'value',...
        images_str = ",".join([f"{k}:'{v}'" for k, v in images_dict.items()])

        # Replace placeholder
        html = self._template.replace(self.PLACEHOLDER, images_str)

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
