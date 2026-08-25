"""Profile merging logic."""

from __future__ import annotations

from scripts.domain.models import Source


def merge_sources(
    global_sources: list[Source],
    profile_sources: list[Source] | None,
) -> list[Source]:
    """Merge global and profile sources.

    Rules:
    1. Combine global + profile sources
    2. Profile overrides global on ID collision
    3. Profile can disable global sources via enabled=False
    """
    if profile_sources is None:
        return list(global_sources)

    # Build a dict of profile sources by ID for override lookup
    profile_by_id = {s.id: s for s in profile_sources}

    result = []
    seen_ids = set()

    # Process global sources, applying profile overrides
    for gs in global_sources:
        if gs.id in profile_by_id:
            result.append(profile_by_id[gs.id])
        else:
            result.append(gs)
        seen_ids.add(gs.id)

    # Add profile-only sources (not in global)
    for ps in profile_sources:
        if ps.id not in seen_ids:
            result.append(ps)

    return result
