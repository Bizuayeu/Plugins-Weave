"""
Digest merging utilities.

Handles merging of individual digests with deduplication.
"""

from typing import List

from domain.types import IndividualDigestData
from infrastructure import get_structured_logger
from interfaces.provisional.validator import validate_individual_digests_list

_logger = get_structured_logger(__name__)


class DigestMerger:
    """Merges individual digests with deduplication by source_file."""

    @staticmethod
    def merge(
        existing_digests: List[IndividualDigestData],
        new_digests: List[IndividualDigestData],
    ) -> List[IndividualDigestData]:
        """
        Merge existing and new individual digests.

        Deduplication is based on source_file key. When duplicates exist,
        new digests overwrite existing ones.

        Args:
            existing_digests: Existing individual digests list
            new_digests: New individual digests to merge

        Returns:
            Merged list of individual digests

        Raises:
            ValidationError: If any digest is missing 'source_file' key
        """
        # Validate inputs
        validate_individual_digests_list(existing_digests, context="existing")
        validate_individual_digests_list(new_digests, context="new")

        # Create dict keyed by source_file
        merged_dict = {d["source_file"]: d for d in existing_digests}

        # Overwrite with new digests
        for new_digest in new_digests:
            source_file = new_digest["source_file"]
            if source_file in merged_dict:
                _logger.info(f"Overwriting existing digest: {source_file}")
            merged_dict[source_file] = new_digest

        return list(merged_dict.values())
