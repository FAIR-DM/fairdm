"""Signed, time-limited claim tokens."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

if TYPE_CHECKING:
    from fairdm.contrib.contributors.models import Person

_DEFAULT_MAX_AGE = 7 * 24 * 60 * 60
_DEFAULT_SALT = "fairdm.contributor.claim"


def _get_signer() -> TimestampSigner:
    salt = getattr(settings, "CLAIM_TOKEN_SALT", _DEFAULT_SALT)
    return TimestampSigner(salt=salt)


def _get_max_age() -> int:
    return getattr(settings, "CLAIM_TOKEN_MAX_AGE", _DEFAULT_MAX_AGE)


def generate_claim_token(person: Person) -> str:
    """Generate a signed, time-stamped claim token for a person.

    The token holds the person's primary key and is validated by its signature, so nothing is stored.

    Args:
        person: The person to generate the token for.

    Returns:
        The signed token string.
    """
    signer = _get_signer()
    return signer.sign(str(person.pk))


def validate_claim_token(token_string: str) -> Person | None:
    """Validate a claim token and return the unclaimed person it names.

    Args:
        token_string: The signed token from ``generate_claim_token``.

    Returns:
        The person the token names, who has not yet claimed their profile.

    Raises:
        ClaimingError: The signature is invalid, the token is older than ``CLAIM_TOKEN_MAX_AGE``,
            no person matches, or the person has already claimed their profile.
    """
    from fairdm.contrib.contributors.exceptions import ClaimingError
    from fairdm.contrib.contributors.models import Person

    signer = _get_signer()
    max_age = _get_max_age()

    try:
        pk_str = signer.unsign(token_string, max_age=max_age)
    except SignatureExpired as exc:
        raise ClaimingError("Claim token has expired.") from exc
    except BadSignature as exc:
        raise ClaimingError(
            "Claim token is invalid or has been tampered with."
        ) from exc

    try:
        person = Person.objects.get(pk=pk_str)
    except Person.DoesNotExist as exc:
        raise ClaimingError("No Person found for this claim token.") from exc

    if person.is_claimed:
        raise ClaimingError("This profile has already been claimed.")

    return person
