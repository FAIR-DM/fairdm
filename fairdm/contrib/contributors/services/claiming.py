"""Claiming services that activate an unclaimed person by ORCID, email or token.

Expected, user-facing failures raise ``ClaimingError``. Programmer errors propagate unchanged.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin

    from fairdm.contrib.contributors.models import Person


def claim_via_orcid(person: Person, sociallogin: SocialLogin) -> Person:
    """Activate an unclaimed person through an ORCID social login.

    The person is marked claimed and active, the social login is connected to them,
    and the outcome is written to the claiming audit log, failures included.

    Args:
        person: The unclaimed person to activate.
        sociallogin: The allauth social login for the ORCID account.

    Returns:
        The now-claimed person.

    Raises:
        ClaimingError: The person is already claimed or deactivated.
    """
    from fairdm.contrib.contributors.exceptions import ClaimingError
    from fairdm.contrib.contributors.models import ClaimMethod
    from fairdm.contrib.contributors.utils.audit import log_claiming_event

    orcid_uid = getattr(getattr(sociallogin, "account", None), "uid", "")

    if person.is_claimed:
        log_claiming_event(
            method=ClaimMethod.ORCID,
            source=person,
            target=None,
            success=False,
            failure_reason="Person is already claimed.",
            details={"orcid": orcid_uid},
        )
        raise ClaimingError("This profile has already been claimed.")

    if not person.is_active:
        log_claiming_event(
            method=ClaimMethod.ORCID,
            source=person,
            target=None,
            success=False,
            failure_reason="Person is banned (is_active=False).",
            details={"orcid": orcid_uid},
        )
        raise ClaimingError("This profile is banned and cannot be claimed.")

    person.is_claimed = True
    person.is_active = True
    person.save(update_fields=["is_claimed", "is_active"])

    sociallogin.connect(
        sociallogin.request if hasattr(sociallogin, "request") else None, person
    )

    log_claiming_event(
        method=ClaimMethod.ORCID,
        source=person,
        target=person,
        success=True,
        details={"orcid": orcid_uid},
    )

    return person


def claim_via_email(person: Person) -> Person | None:
    """Activate an unclaimed person after email verification.

    Does nothing unless ``ACCOUNT_EMAIL_VERIFICATION`` is ``mandatory``, so a signal handler
    can call it without checking. The outcome is written to the claiming audit log.

    Args:
        person: The unclaimed person to activate.

    Returns:
        The now-claimed person, or None when verification is not mandatory.

    Raises:
        ClaimingError: The person is already claimed or deactivated.
    """
    from django.conf import settings

    from fairdm.contrib.contributors.exceptions import ClaimingError
    from fairdm.contrib.contributors.models import ClaimMethod
    from fairdm.contrib.contributors.utils.audit import log_claiming_event

    if getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") != "mandatory":
        return None

    if person.is_claimed:
        log_claiming_event(
            method=ClaimMethod.EMAIL,
            source=person,
            target=None,
            success=False,
            failure_reason="Person is already claimed.",
        )
        raise ClaimingError("This profile has already been claimed.")

    if not person.is_active:
        log_claiming_event(
            method=ClaimMethod.EMAIL,
            source=person,
            target=None,
            success=False,
            failure_reason="Person is banned (is_active=False).",
        )
        raise ClaimingError("This profile is banned and cannot be claimed.")

    person.is_claimed = True
    person.is_active = True
    person.save(update_fields=["is_claimed", "is_active"])

    log_claiming_event(
        method=ClaimMethod.EMAIL,
        source=person,
        target=person,
        success=True,
    )

    return person


def claim_via_token(token_string: str, user: Person) -> Person:
    """Activate an unclaimed person through a signed claim token.

    This is the simple path, for a user with no conflicting account. Merging two accounts
    is routed to ``merge_persons`` by the claim view. The outcome is written to the
    claiming audit log.

    Args:
        token_string: The signed token from ``generate_claim_token``.
        user: The authenticated person claiming the profile.

    Returns:
        The now-claimed person.

    Raises:
        ClaimingError: The token is tampered, expired or already used, or its person is deactivated.
    """
    from fairdm.contrib.contributors.exceptions import ClaimingError
    from fairdm.contrib.contributors.models import ClaimMethod
    from fairdm.contrib.contributors.utils.audit import log_claiming_event
    from fairdm.contrib.contributors.utils.tokens import validate_claim_token

    try:
        person = validate_claim_token(token_string)
    except ClaimingError as exc:
        log_claiming_event(
            method=ClaimMethod.TOKEN,
            source=None,
            target=None,
            initiated_by=user,
            success=False,
            failure_reason=str(exc),
        )
        raise

    if not person.is_active:
        reason = "Person is banned (is_active=False)."
        log_claiming_event(
            method=ClaimMethod.TOKEN,
            source=person,
            target=None,
            initiated_by=user,
            success=False,
            failure_reason=reason,
        )
        raise ClaimingError("This profile is banned and cannot be claimed.")

    person.is_claimed = True
    person.is_active = True
    person.save(update_fields=["is_claimed", "is_active"])

    log_claiming_event(
        method=ClaimMethod.TOKEN,
        source=person,
        target=person,
        initiated_by=user,
        success=True,
    )

    return person
