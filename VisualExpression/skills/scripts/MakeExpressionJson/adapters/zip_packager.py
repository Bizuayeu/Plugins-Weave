"""ZIP packaging for skill distribution."""

import zipfile
from pathlib import Path
from typing import List, Optional


class ZipPackager:
    """Creates ZIP packages for skill distribution."""

    def __init__(self, output_dir: Optional[str] = None):
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
        output_name: str = "VisualExpression_skills.zip",
        additional_files: Optional[List[Path]] = None,
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

        Returns:
            Path to the created ZIP file
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.output_dir / output_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add main skill file
            if skill_md_path.exists():
                zf.write(skill_md_path, "skills/SKILL.md")

            # Add HTML files
            if html_path.exists():
                zf.write(html_path, "skills/VisualExpressionUI.html")

            if template_path.exists():
                zf.write(template_path, "skills/VisualExpressionUI.template.html")

            # Add JSON
            if json_path.exists():
                zf.write(json_path, "skills/ExpressionImages.json")

            # Add additional files
            if additional_files:
                for file_path in additional_files:
                    if file_path.exists():
                        # Preserve relative structure under skills/
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
        self.output_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.output_dir / output_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if html_path.exists():
                zf.write(html_path, "VisualExpressionUI.html")

        return zip_path
