"""Skills directory locator for MakeExpressionJson.

Extracted from FileHandler to maintain single responsibility principle.
"""

import os
from pathlib import Path

from .file_constants import (
    DEFAULT_TEMPLATE_FILENAME,
    SKILLS_DIR_ENV_VAR,
    SKILLS_DIR_MARKERS,
)


class SkillsLocator:
    """Locates the skills directory and template files.

    This class handles the logic for finding the skills directory,
    supporting multiple detection strategies:
    1. Explicit path parameter (highest priority)
    2. Environment variable
    3. Upward marker file search
    4. Relative path fallback
    """

    def __init__(self, skills_dir: str | Path | None = None):
        """
        Initialize the skills locator.

        Args:
            skills_dir: Explicit skills directory path (overrides auto-detection).
                       Can be a string or Path object.
        """
        if skills_dir is not None:
            self._skills_dir: Path | None = Path(skills_dir)
        else:
            self._skills_dir = None

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
        if self._skills_dir is not None:
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
