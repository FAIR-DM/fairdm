"""Core claiming service functions.

All public functions raise ClaimingError for expected, user-facing failure conditions
(banned person, already claimed, expired token, etc.).  Unexpected programmer errors
still propagate as ValueError or similar.

Claiming pathways implemented here:
  - claim_via_orcid   (US1 — ORCID social login)
  - claim_via_email   (US2 — email verification)
  - claim_via_token   (US3 — admin-generated token link)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin

    from fairdm.contrib.contributors.models import Person


def claim_via_orcid(person: Person, sociallogin: SocialLogin) -> Person:
    """Activate an unclaimed Person via ORCID social login.

    Guards:
      - Raises ClaimingError if person.is_claimed is True.
      - Raises ClaimingError if person.is_active is False (banned — FR-017).

    On success:
      - Sets is_claimed=True and is_active=True.
      - Connects the SocialLogin to the person.
      - Writes a success ClaimingAuditLog record.

    On expected failure:
      - Writes a failure ClaimingAuditLog record.
      - Re-raises ClaimingError.

    Args:
        person: The unclaimed Person to activate.
        sociallogin: The allauth SocialLogin object for the ORCID account.

    Returns:
        The now-claimed Person instance.

    Raises:
        ClaimingError: If the person is already claimed or banned.
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

    # Activate and claim
    person.is_claimed = True
    person.is_active = True
    person.save(update_fields=["is_claimed", "is_active"])

    # Connect the social account
    sociallogin.connect(sociallogin.request if hasattr(sociallogin, "request") else None, person)

    log_claiming_event(
        method=ClaimMethod.ORCID,
        source=person,
        target=person,
        success=True,
        details={"orcid": orcid_uid},
    )

    return person


def claim_via_email(person: Person) -> Person | None:
    """Activate an unclaimed Person after email verification.

    This function is a silent no-op (returns None) when
    ACCOUNT_EMAIL_VERIFICATION != 'mandatory', so the signal handler can safely
    call it without checking the setting.

    Guards:
      - Silent no-op when ACCOUNT_EMAIL_VERIFICATION != 'mandatory'.
      - Raises ClaimingError if person.is_claimed is True.
      - Raises ClaimingError if person.is_active is False (banned — FR-017).

    On success:
      - Sets is_claimed=True and is_active=True.
      - Writes a success ClaimingAuditLog record.

    On expected failure:
      - Writes a failure ClaimingAuditLog record.
      - Re-raises ClaimingError.

    Args:
        person: The unclaimed Person to activate.

    Returns:
        The now-claimed Person instance, or None if the guard short-circuited.

    Raises:
        ClaimingError: If not in mandatory-verification mode, or person is banned/claimed.
    """
    from django.conf import settings

    from fairdm.contrib.contributors.exceptions import ClaimingError
    from fairdm.contrib.contributors.models import ClaimMethod
    from fairdm.contrib.contributors.utils.audit import log_claiming_event

    # Silent no-op when verification is not mandatory
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
    """Activate an unclaimed Person via a signed admin-generated claim token.

    This handles the *simple-claim path only*: the calling user has no
    conflicting active Person account.  The merge path (authenticated Person B
    claiming a token belonging to unclaimed Person A) is routed by ClaimProfileView
    directly to merge_persons() — the view is the routing layer.

    Guards:
      - Raises ClaimingError on tampered or expired tokens (via validate_claim_token).
      - Raises ClaimingError if the token resolves to a banned Person (FR-017).
      - Raises ClaimingError if the token resolves to an already-claimed Person.

    On success:
      - Sets is_claimed=True and is_active=True.
      - Writes a success ClaimingAuditLog record.

    On expected failure:
      - Writes a failure ClaimingAuditLog record.
      - Re-raises ClaimingError.

    Args:
        token_string: The signed token string generated by generate_claim_token().
        user: The authenticated Person who is claiming the profile.

    Returns:
        The now-claimed Person instance.

    Raises:
        ClaimingError: On any token validation failure or policy violation.
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

    # Banned person guard (FR-017)
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
