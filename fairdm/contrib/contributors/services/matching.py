"""Fuzzy name matching that finds potential duplicate people."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rapidfuzz.fuzz import token_sort_ratio

if TYPE_CHECKING:
    from fairdm.contrib.contributors.models import Person


def find_duplicate_candidates(person: Person, threshold: float = 0.85) -> list[dict]:
    """Find people whose names closely match this person's name.

    Scores use rapidfuzz ``token_sort_ratio``, so reordered names such as
    "Smith, John" and "John Smith" score alike.

    Args:
        person: The person to find duplicates for.
        threshold: Minimum similarity score between 0 and 1.

    Returns:
        ``{"person": Person, "score": float}`` dicts with a score from 0 to 1, highest
        first. The person itself is excluded.
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
        raw_score = token_sort_ratio(query_name, candidate_name)
        score = raw_score / 100.0
        if score >= threshold:
            candidates.append({"person": candidate, "score": score})

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates
