"""Tests for the fuzzy name matching service."""

import pytest


@pytest.fixture
def john_smith(db):
    from fairdm.factories import PersonFactory

    return PersonFactory(name="John Smith")


@pytest.fixture
def john_a_smith(db):
    from fairdm.factories import PersonFactory

    return PersonFactory(name="John A. Smith")


@pytest.fixture
def alice_brown(db):
    from fairdm.factories import PersonFactory

    return PersonFactory(name="Alice Brown")


class TestFindDuplicateCandidates:
    def test_similar_names_surface_above_threshold(self, db, john_smith, john_a_smith):
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )

        candidates = find_duplicate_candidates(john_a_smith)
        result_persons = [c["person"] for c in candidates]
        assert john_smith in result_persons

    def test_similar_name_score_above_threshold(self, db, john_smith, john_a_smith):
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )

        candidates = find_duplicate_candidates(john_a_smith)
        john_smith_entry = next(
            (c for c in candidates if c["person"] == john_smith), None
        )
        assert john_smith_entry is not None
        assert john_smith_entry["score"] >= 0.85

    def test_dissimilar_names_excluded(self, db, john_a_smith, alice_brown):
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )

        candidates = find_duplicate_candidates(john_a_smith)
        result_persons = [c["person"] for c in candidates]
        assert alice_brown not in result_persons

    def test_self_excluded_from_results(self, db, john_a_smith):
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )

        candidates = find_duplicate_candidates(john_a_smith)
        result_persons = [c["person"] for c in candidates]
        assert john_a_smith not in result_persons

    def test_name_reordering_handled(self, db):
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )
        from fairdm.factories import PersonFactory

        person_a = PersonFactory(name="John Smith")
        person_b = PersonFactory(name="Smith John")
        candidates = find_duplicate_candidates(person_a)
        result_persons = [c["person"] for c in candidates]
        assert person_b in result_persons

    def test_results_sorted_by_score_descending(self, db, john_a_smith):
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )
        from fairdm.factories import PersonFactory

        PersonFactory(name="John Smith")
        PersonFactory(name="J. Smith")
        candidates = find_duplicate_candidates(john_a_smith)
        scores = [c["score"] for c in candidates]
        assert scores == sorted(scores, reverse=True)

    def test_custom_threshold_respected(self, db, john_smith, alice_brown):
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )

        candidates = find_duplicate_candidates(john_smith, threshold=0.0)
        result_persons = [c["person"] for c in candidates]
        assert len(candidates) >= 1

    def test_empty_results_when_no_matches(self, db):
        from fairdm.contrib.contributors.services.matching import (
            find_duplicate_candidates,
        )
        from fairdm.factories import PersonFactory

        unique_person = PersonFactory(name="Qxzrptlm Bvnwzxqk")
        candidates = find_duplicate_candidates(unique_person)
        assert candidates == []
