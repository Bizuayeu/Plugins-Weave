"""
File management utilities for provisional digests.

Handles file I/O operations, numbering, and directory management.
"""

from pathlib import Path
from typing import Any

from application.config import DigestConfig
from domain.constants import LEVEL_CONFIG
from domain.error_formatter import get_error_formatter
from domain.exceptions import ConfigError
from domain.file_naming import find_max_number, format_digest_number
from domain.types import LevelConfigData
from infrastructure import load_json


class ProvisionalFileManager:
    """Manages provisional digest file operations."""

    def __init__(self, config: DigestConfig | None = None) -> None:
        """
        Initialize the file manager.

        Args:
            config: DigestConfig instance (injected for testability)

        Example:
            >>> manager = ProvisionalFileManager()
            >>> manager.get_current_digest_number("weekly")
        """
        self.config = config or DigestConfig()
        self.level_config = LEVEL_CONFIG

    def get_current_digest_number(self, level: str) -> int | None:
        """
        Get the current provisional digest file number for a level.

        Args:
            level: Digest level (weekly, monthly, etc.)

        Returns:
            Current file number if exists, None otherwise

        Raises:
            ConfigError: If level is invalid

        Example:
            >>> manager = ProvisionalFileManager(config)
            >>> manager.get_current_digest_number("weekly")
            42
        """
        level_cfg = self._get_level_config(level)
        prefix = str(level_cfg["prefix"])
        provisional_dir = self.config.get_provisional_dir(level)

        # Search for Individual files in provisional directory
        pattern = f"{prefix}[0-9]*_Individual.txt"
        existing_files = list(provisional_dir.glob(pattern))

        if not existing_files:
            return None

        # Cast to expected type for find_max_number
        files_for_search: list[Path | str] = list(existing_files)
        return find_max_number(files_for_search, prefix)

    def load_existing_provisional(self, level: str, digest_num: int) -> dict[str, Any] | None:
        """
        Load an existing provisional digest file.

        Args:
            level: Digest level
            digest_num: Digest number

        Returns:
            Loaded provisional data, or None if file doesn't exist

        Raises:
            ConfigError: If level is invalid

        Example:
            >>> manager.load_existing_provisional("weekly", 42)
            {"individual_digests": [...]}
        """
        self._get_level_config(level)  # Validate level

        filename = f"{format_digest_number(level, digest_num)}_Individual.txt"
        provisional_dir = self.config.get_provisional_dir(level)
        file_path = provisional_dir / filename

        if not file_path.exists():
            return None

        return load_json(file_path)

    def get_provisional_path(self, level: str, digest_num: int) -> Path:
        """
        Get the file path for a provisional digest.

        Args:
            level: Digest level
            digest_num: Digest number

        Returns:
            Path to the provisional file

        Example:
            >>> manager = ProvisionalFileManager(config)
            >>> path = manager.get_provisional_path("weekly", 42)
            >>> path.name
            'W0042_Individual.txt'
        """
        formatted_num = format_digest_number(level, digest_num)
        filename = f"{formatted_num}_Individual.txt"
        provisional_dir = self.config.get_provisional_dir(level)
        provisional_dir.mkdir(parents=True, exist_ok=True)
        return provisional_dir / filename

    def get_digits_for_level(self, level: str) -> int:
        """
        Get the number of digits for a level's numbering.

        Args:
            level: Digest level

        Returns:
            Number of digits for formatting

        Example:
            >>> manager.get_digits_for_level("weekly")
            4
        """
        level_cfg = self._get_level_config(level)
        return int(level_cfg["digits"])

    def _get_level_config(self, level: str) -> LevelConfigData:
        """
        Get and validate level configuration.

        Args:
            level: Digest level

        Returns:
            Level configuration dictionary

        Raises:
            ConfigError: If level is invalid

        Example:
            >>> manager._get_level_config("weekly")
            {"prefix": "W", "digits": 4, "dir": "Weekly", ...}
        """
        level_cfg = self.level_config.get(level)
        if not level_cfg:
            formatter = get_error_formatter()
            raise ConfigError(formatter.config.invalid_level(level, list(self.level_config.keys())))
        return level_cfg
