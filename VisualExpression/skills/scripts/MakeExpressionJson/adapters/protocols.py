"""Protocol definitions for adapters layer.

Defines abstract interfaces for dependency injection and testing.
"""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SkillsLocatorProtocol(Protocol):
    """Protocol for skills directory location.

    Implementations should provide methods to locate the skills directory
    and the default template file.
    """

    def get_skills_dir(self) -> Path:
        """Get the skills directory path.

        Returns:
            Path to the skills directory
        """
        ...

    def get_default_template_path(self) -> Path:
        """Get the default template path.

        Returns:
            Path to VisualExpressionUI.template.html
        """
        ...


@runtime_checkable
class FileWriterProtocol(Protocol):
    """Protocol for file writing operations.

    Implementations should provide methods for writing JSON and HTML files,
    reading templates, and managing output directories.
    """

    def write_json(
        self,
        data: dict[str, Any],
        filename: str = ...,
    ) -> Path:
        """Write JSON data to file.

        Args:
            data: Dictionary to serialize
            filename: Output filename

        Returns:
            Path to the written file
        """
        ...

    def write_html(
        self,
        content: str,
        filename: str = ...,
    ) -> Path:
        """Write HTML content to file.

        Args:
            content: HTML content to write
            filename: Output filename

        Returns:
            Path to the written file
        """
        ...

    def read_template(self, template_path: str) -> str:
        """Read template file content.

        Args:
            template_path: Path to the template file

        Returns:
            Template content as string
        """
        ...

    def ensure_output_dir(self) -> Path:
        """Ensure output directory exists.

        Returns:
            Path to the output directory
        """
        ...
