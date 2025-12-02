"""
Provisional digest validation utilities.

Centralizes all validation logic for provisional digest data structures.
"""

from typing import Any, List, cast

from domain.error_formatter import get_error_formatter
from domain.exceptions import ValidationError
from domain.types import IndividualDigestData
from domain.validators import is_valid_dict, is_valid_list


def validate_long_short_text(value: Any, field_name: str, index: int) -> None:
    """
    Validate abstract/impression field format.

    Accepts only {long, short} format.

    Args:
        value: The value to validate
        field_name: Name of the field ("abstract" or "impression")
        index: Index of the digest in the list (for error messages)

    Raises:
        ValidationError: If value is not {long: str, short: str} format
    """
    if value is None:
        return  # Optional field

    if not isinstance(value, dict):
        raise ValidationError(
            f"{field_name} at index {index} must be {{long: str, short: str}}, "
            f"got {type(value).__name__}"
        )

    if "long" not in value or "short" not in value:
        raise ValidationError(
            f"{field_name} at index {index} must have both 'long' and 'short' keys"
        )

    if not isinstance(value["long"], str) or not isinstance(value["short"], str):
        raise ValidationError(
            f"{field_name} at index {index}: 'long' and 'short' must be strings"
        )


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
    formatter = get_error_formatter()
    if not is_valid_dict(digest):
        raise ValidationError(
            formatter.validation.invalid_type(f"{prefix}digest at index {index}", "dict", digest)
        )
    if "source_file" not in digest:
        raise ValidationError(
            formatter.validation.validation_error(
                f"{prefix}digest at index {index}", "missing 'source_file' key", None
            )
        )

    # Validate abstract/impression format ({long, short} required)
    validate_long_short_text(digest.get("abstract"), "abstract", index)
    validate_long_short_text(digest.get("impression"), "impression", index)


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
        return cast(List[IndividualDigestData], data)

    # Data is a dict with "individual_digests" key
    if is_valid_dict(data) and "individual_digests" in data:
        return cast(List[IndividualDigestData], data["individual_digests"])

    # Invalid format
    formatter = get_error_formatter()
    raise ValidationError(
        formatter.validation.invalid_type(
            "input format", "list or dict with 'individual_digests' key", data
        )
    )
