"""Tests for claim token utilities.

Tests generate_claim_token() and validate_claim_token() from utils/tokens.py.
These test stubs depend on T006 (tokens.py) which is already implemented in Phase 2.
"""

import time

import pytest

from fairdm.contrib.contributors.exceptions import ClaimingError
from fairdm.contrib.contributors.models import Person
from fairdm.contrib.contributors.utils.tokens import generate_claim_token, validate_claim_token


@pytest.fixture
def unclaimed_person(db):
    """Unclaimed Person in Ghost state."""
    return Person.objects.create_unclaimed(first_name="Token", last_name="Test")


@pytest.fixture
def claimed_person(db):
    """Already-claimed Person."""
    from fairdm.factories import PersonFactory

    p = PersonFactory(email="claimed@example.com", is_active=True, is_claimed=True)
    p.set_password("testpass123")
    p.save()
    return p


class TestGenerateClaimToken:
    def test_returns_string(self, db, unclaimed_person):
        """generate_claim_token returns a non-empty string."""
        token = generate_claim_token(unclaimed_person)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_different_persons_produce_different_tokens(self, db, unclaimed_person):
        """Each person produces a unique token."""
        person2 = Person.objects.create_unclaimed(first_name="Other", last_name="Person")
        token1 = generate_claim_token(unclaimed_person)
        token2 = generate_claim_token(person2)
        assert token1 != token2


class TestValidateClaimToken:
    def test_round_trip_returns_correct_person(self, db, unclaimed_person):
        """validate_claim_token(generate_claim_token(p)) returns p."""
        token = generate_claim_token(unclaimed_person)
        result = validate_claim_token(token)
        assert result is not None
        assert result.pk == unclaimed_person.pk

    def test_expired_token_raises_claiming_error(self, db, unclaimed_person, settings):
        """validate_claim_token raises ClaimingError when token has expired."""
        settings.CLAIM_TOKEN_MAX_AGE = 0  # Expire immediately
        token = generate_claim_token(unclaimed_person)
        time.sleep(0.01)

        with pytest.raises(ClaimingError, match="expired"):
            validate_claim_token(token)

    def test_tampered_token_raises_claiming_error(self, db, unclaimed_person):
        """validate_claim_token raises ClaimingError for tampered tokens."""
        with pytest.raises(ClaimingError):
            validate_claim_token("tampered.token.string")

    def test_hmac_modified_token_raises_claiming_error(self, db, unclaimed_person):
        """validate_claim_token raises ClaimingError when HMAC is modified."""
        token = generate_claim_token(unclaimed_person)
        # Corrupt the signature portion
        parts = token.rsplit(":", 1)
        corrupted = parts[0] + ":AAAAAAAAAAAAAAAA"

        with pytest.raises(ClaimingError):
            validate_claim_token(corrupted)

    def test_already_claimed_person_raises_claiming_error(self, db, unclaimed_person):
        """validate_claim_token raises ClaimingError if person was already claimed after token was issued."""
        token = generate_claim_token(unclaimed_person)
        # Simulate person being claimed after token was issued
        unclaimed_person.is_claimed = True
        unclaimed_person.save()

        with pytest.raises(ClaimingError, match="already been claimed"):
            validate_claim_token(token)

    def test_banned_person_returns_none_or_person(self, db):
        """validate_claim_token returns a Person with is_active=False (banned) — the view layer handles this."""
        from fairdm.factories import PersonFactory

        banned = PersonFactory(email=None, is_active=False, is_claimed=False)
        token = generate_claim_token(banned)
        result = validate_claim_token(token)
        # Result is the person — callers (e.g., claim_via_token) must check is_active
        assert result is not None
        assert result.pk == banned.pk
        assert result.is_active is False
