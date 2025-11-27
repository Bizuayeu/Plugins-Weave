"""
Provisional digest validation utilities.

Centralizes all validation logic for provisional digest data structures.
"""

from typing import Any, List

from application.validators import is_valid_dict, is_valid_list
from domain.exceptions import ValidationError
from domain.types import IndividualDigestData, ProvisionalDigestFile


def validate_individual_digest(digest: Any, index: int, context: str = "") -> None:
    """
    Validate a single individual digest entry.

    Args:
        digest: The digest data to validate
        index: Index of the digest in the list (for error messages)
        context: Additional context for error messages (e.g., "existing", "new")

    Raises:
        ValidationError: If validation fails
    """
    prefix = f"{context} " if context else ""
    if not is_valid_dict(digest):
        raise ValidationError(
            f"Invalid {prefix}digest at index {index}: expected dict, got {type(digest).__name__}"
        )
    if "source_file" not in digest:
        raise ValidationError(
            f"Invalid {prefix}digest at index {index}: missing 'source_file' key"
        )


def validate_individual_digests_list(
    digests: List[IndividualDigestData], context: str = ""
) -> None:
    """
    Validate a list of individual digests.

    Args:
        digests: List of digest data to validate
        context: Additional context for error messages

    Raises:
        ValidationError: If any digest fails validation
    """
    for i, digest in enumerate(digests):
        validate_individual_digest(digest, i, context)


def validate_provisional_structure(data: Any) -> List[IndividualDigestData]:
    """
    Validate and extract individual_digests from provisional data structure.

    Args:
        data: The loaded provisional data (should be a dict)

    Returns:
        List of individual digests, empty list if structure is invalid

    Note:
        This function logs warnings for invalid structures but does not raise.
        It returns an empty list for graceful degradation.
    """
    from infrastructure import log_warning

    if not is_valid_dict(data):
        log_warning("Invalid existing data format, ignoring")
        return []

    individual_digests = data.get("individual_digests", [])
    if not is_valid_list(individual_digests):
        log_warning("Invalid individual_digests format, ignoring")
        return []

    return individual_digests


def validate_input_format(data: Any) -> List[IndividualDigestData]:
    """
    Validate parsed input data and extract individual digests.

    Args:
        data: Parsed JSON data (list or dict)

    Returns:
        List of individual digests

    Raises:
        ValidationError: If data format is invalid
    """
    # Data is a list: return directly
    if is_valid_list(data):
        return data

    # Data is a dict with "individual_digests" key
    if is_valid_dict(data) and "individual_digests" in data:
        return data["individual_digests"]

    # Invalid format
    raise ValidationError(
        f"Invalid input format. Expected list or dict with 'individual_digests' key. "
        f"Got: {type(data).__name__}"
    )
