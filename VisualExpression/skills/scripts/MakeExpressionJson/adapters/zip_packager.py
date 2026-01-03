"""ZIP packaging for skill distribution."""

import logging
import zipfile
from pathlib import Path

from .file_handler import ensure_dir

logger = logging.getLogger(__name__)


class ZipPackager:
    """Creates ZIP packages for skill distribution."""

    def __init__(self, output_dir: str | None = None):
        """
        Initialize the zip packager.

        Args:
            output_dir: Directory for output ZIP file
        """
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()

    def create_skill_zip(
        self,
        skill_md_path: Path,
        html_path: Path,
        template_path: Path,
        json_path: Path,
        output_name: str = "VisualExpressionSkills.zip",
        additional_files: list[Path] | None = None,
        strict: bool = True,
    ) -> Path:
        """
        Create a ZIP package containing the skill files.

        Args:
            skill_md_path: Path to SKILL.md
            html_path: Path to built HTML
            template_path: Path to HTML template
            json_path: Path to expression JSON
            output_name: Name of the output ZIP file
            additional_files: Additional files to include
            strict: If True, raise FileNotFoundError for missing required files

        Returns:
            Path to the created ZIP file

        Raises:
            FileNotFoundError: If strict=True and required files are missing
        """
        ensure_dir(self.output_dir)
        zip_path = self.output_dir / output_name

        def _check_file(file_path: Path, arcname: str, required: bool = False) -> bool:
            """Check if file exists and log/raise if not."""
            if file_path.exists():
                return True
            msg = f"File not found: {file_path}"
            logger.warning(msg)
            if strict and required:
                raise FileNotFoundError(msg)
            return False

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add main skill file
            if _check_file(skill_md_path, "skills/SKILL.md"):
                zf.write(skill_md_path, "skills/SKILL.md")

            # Add HTML files (required)
            if _check_file(html_path, "skills/VisualExpressionUI.html", required=True):
                zf.write(html_path, "skills/VisualExpressionUI.html")

            if _check_file(template_path, "skills/VisualExpressionUI.template.html"):
                zf.write(template_path, "skills/VisualExpressionUI.template.html")

            # Add JSON (required)
            if _check_file(json_path, "skills/ExpressionImages.json", required=True):
                zf.write(json_path, "skills/ExpressionImages.json")

            # Add additional files
            if additional_files:
                for file_path in additional_files:
                    if _check_file(file_path, f"skills/{file_path.name}"):
                        arcname = f"skills/{file_path.name}"
                        zf.write(file_path, arcname)

        return zip_path

    def create_minimal_zip(
        self,
        html_path: Path,
        output_name: str = "VisualExpression_minimal.zip",
    ) -> Path:
        """
        Create a minimal ZIP with just the built HTML.

        Args:
            html_path: Path to built HTML
            output_name: Name of the output ZIP file

        Returns:
            Path to the created ZIP file
        """
        ensure_dir(self.output_dir)
        zip_path = self.output_dir / output_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if html_path.exists():
                zf.write(html_path, "VisualExpressionUI.html")

        return zip_path
