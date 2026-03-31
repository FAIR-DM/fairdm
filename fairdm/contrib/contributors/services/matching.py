"""
Fuzzy name matching service for identifying potential duplicate Person records.

Uses rapidfuzz token_sort_ratio so that name-token reordering (e.g. "Smith, John"
vs "John Smith") does not lower the similarity score.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rapidfuzz.fuzz import token_sort_ratio

if TYPE_CHECKING:
    from fairdm.contrib.contributors.models import Person


def find_duplicate_candidates(person: Person, threshold: float = 0.85) -> list[dict]:
    """Return a list of potential duplicate Person records for *person*.

    Each entry in the returned list is a dict with keys:
        - ``person``:  the candidate :class:`Person` instance
        - ``score``:   normalised similarity score in the range [0, 1]

    Only entries with ``score >= threshold`` are included.  The list is sorted
    by score descending. *person* itself is always excluded.

    Args:
        person: The Person to find duplicates for.
        threshold: Minimum similarity score (0-1). Defaults to 0.85.

    Returns:
        List of ``{"person": Person, "score": float}`` dicts, sorted by score desc.
    """
    from fairdm.contrib.contributors.models import Person as PersonModel

    query_name = (person.name or "").strip()
    if not query_name:
        return []

    candidates: list[dict] = []
    for candidate in PersonModel.objects.exclude(pk=person.pk).only("pk", "name"):
        candidate_name = (candidate.name or "").strip()
        if not candidate_name:
            continue
        # token_sort_ratio returns 0-100; normalise to 0-1
        raw_score = token_sort_ratio(query_name, candidate_name)
        score = raw_score / 100.0
        if score >= threshold:
            candidates.append({"person": candidate, "score": score})

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates
