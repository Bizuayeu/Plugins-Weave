"""
Provisional digest handling submodule.

This submodule provides modular components for managing provisional digest files:
- input_loader: JSON input parsing and validation
- file_manager: File I/O and numbering operations
- merger: Digest merging logic
- validator: Data validation utilities
"""

from interfaces.provisional.input_loader import InputLoader
from interfaces.provisional.file_manager import ProvisionalFileManager
from interfaces.provisional.merger import DigestMerger
from interfaces.provisional.validator import (
    validate_individual_digest,
    validate_individual_digests_list,
    validate_input_format,
    validate_provisional_structure,
)

__all__ = [
    "InputLoader",
    "ProvisionalFileManager",
    "DigestMerger",
    # Validator functions
    "validate_individual_digest",
    "validate_individual_digests_list",
    "validate_input_format",
    "validate_provisional_structure",
]
