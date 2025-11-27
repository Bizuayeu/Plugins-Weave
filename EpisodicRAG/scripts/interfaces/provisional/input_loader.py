"""
Input loading utilities for provisional digests.

Handles JSON parsing from files or strings.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from domain.exceptions import ValidationError
from domain.types import IndividualDigestData
from interfaces.provisional.validator import validate_input_format

# Type alias for JSON data
JsonData = Union[Dict[str, Any], List[Any]]


class InputLoader:
    """Loads individual digests from various input sources."""

    @staticmethod
    def load(input_data: str) -> List[IndividualDigestData]:
        """
        Load individual_digests from a JSON file path or JSON string.

        Args:
            input_data: JSON file path or JSON string

        Returns:
            List of individual digests

        Raises:
            ValidationError: If input_data is empty or invalid format
            FileNotFoundError: If file path doesn't exist (when not a valid JSON string)
            json.JSONDecodeError: If JSON parsing fails
        """
        # Empty input check
        if not input_data or not input_data.strip():
            raise ValidationError("input_data cannot be empty")

        # Try as file path first
        input_path = Path(input_data)
        if input_path.exists():
            data = InputLoader._load_from_file(input_path)
        else:
            # Parse as JSON string
            data = InputLoader._parse_json_string(input_data)

        return validate_input_format(data)

    @staticmethod
    def _load_from_file(file_path: Path) -> JsonData:
        """
        Load JSON data from a file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Parsed JSON data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            result: JsonData = json.load(f)
            return result

    @staticmethod
    def _parse_json_string(json_string: str) -> JsonData:
        """
        Parse a JSON string.

        Args:
            json_string: JSON string to parse

        Returns:
            Parsed JSON data
        """
        result: JsonData = json.loads(json_string)
        return result
