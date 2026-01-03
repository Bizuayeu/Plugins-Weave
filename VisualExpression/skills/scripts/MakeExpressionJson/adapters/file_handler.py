"""Backward compatibility module for file_handler.

This module is deprecated. Use file_writer.py and skills_locator.py instead.

The FileHandler functionality has been split into:
- FileWriter: File I/O operations (file_writer.py)
- SkillsLocator: Skills directory location (skills_locator.py)

This module re-exports FileHandler as an alias to FileWriter for
backward compatibility. Existing code will continue to work.
"""

# Re-export for backward compatibility
from .file_writer import FileHandler, FileWriter, ensure_dir
from .skills_locator import SkillsLocator

__all__ = ["FileHandler", "FileWriter", "SkillsLocator", "ensure_dir"]
