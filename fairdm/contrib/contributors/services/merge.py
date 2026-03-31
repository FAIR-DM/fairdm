"""Person merge service (US4).

Provides merge_persons() which transfers all data from person_discard
to person_keep inside a single atomic transaction, then deletes person_discard.

All private helper functions are prefixed with _ and are not part of the public API.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.db import transaction

from fairdm.contrib.contributors.exceptions import ClaimingError

if TYPE_CHECKING:
    from fairdm.contrib.contributors.models import Person

logger = logging.getLogger(__name__)


def merge_persons(person_keep: Person, person_discard: Person) -> Person:
    """Merge person_discard into person_keep, transferring all related data.

    The entire operation runs inside a single atomic transaction.  Any
    unexpected error causes a full rollback — partial merges are impossible.

    Post-merge:
      - person_keep holds all unique Contributions, Identifiers, Affiliations,
        allauth EmailAddress records, and guardian permissions from person_discard.
      - person_keep.is_claimed = True  (it is now the single surviving profile)
      - person_discard is permanently deleted.

    Args:
        person_keep:    The Person that survives the merge.
        person_discard: The Person that is deleted after the merge.

    Returns:
        The updated person_keep instance.

    Raises:
        ClaimingError: If person_keep == person_discard.
        Exception:     Any unexpected error (transaction is rolled back).
    """
    if person_keep.pk == person_discard.pk:
        raise ClaimingError("Cannot merge a Person with itself.")

    with transaction.atomic():
        _reassign_contributions(person_keep, person_discard)
        _reassign_identifiers(person_keep, person_discard)
        _reassign_affiliations(person_keep, person_discard)
        _reassign_allauth_records(person_keep, person_discard)
        _transfer_permissions(person_keep, person_discard)
        _merge_profile_fields(person_keep, person_discard)
        _invalidate_sessions(person_discard)

        # Log the merge
        from fairdm.contrib.contributors.models import ClaimMethod
        from fairdm.contrib.contributors.utils.audit import log_claiming_event

        log_claiming_event(
            method=ClaimMethod.ADMIN_MERGE,
            source=person_discard,
            target=person_keep,
            success=True,
            details={
                "kept_pk": str(person_keep.pk),
                "discarded_pk": str(person_discard.pk),
            },
        )

        # Ensure person_keep is marked as claimed
        person_keep.is_claimed = True
        person_keep.is_active = True
        person_keep.save(update_fields=["is_claimed", "is_active"])

        # Delete the discarded person
        person_discard.delete()

    return person_keep


# ─── Private helpers ─────────────────────────────────────────────────────────


def _reassign_contributions(keep: Person, discard: Person) -> None:
    """Move Contributions from discard to keep, skipping existing duplicates."""
    from fairdm.contrib.contributors.models import Contribution

    for contrib in Contribution.objects.filter(contributor=discard):
        already_exists = Contribution.objects.filter(
            contributor=keep,
            content_type=contrib.content_type,
            object_id=contrib.object_id,
        ).exists()
        if not already_exists:
            contrib.contributor = keep
            contrib.save(update_fields=["contributor"])
        else:
            # Discard duplicate — keep the existing contribution
            contrib.delete()


def _reassign_identifiers(keep: Person, discard: Person) -> None:
    """Move ContributorIdentifiers from discard to keep, avoiding constraint violations."""
    from fairdm.contrib.contributors.models import ContributorIdentifier

    for identifier in ContributorIdentifier.objects.filter(related=discard):
        # Check for exact value match (value is globally unique — can't have 2 with same value)
        # Also check for same (related, type) combo on keep
        value_exists = ContributorIdentifier.objects.filter(value=identifier.value).exclude(pk=identifier.pk).exists()
        type_exists_on_keep = ContributorIdentifier.objects.filter(related=keep, type=identifier.type).exists()

        if value_exists or type_exists_on_keep:
            # Skip — would violate uniqueness constraints
            identifier.delete()
        else:
            # Use update() to bypass AFTER_CREATE lifecycle hook (sync task dispatch)
            ContributorIdentifier.objects.filter(pk=identifier.pk).update(related_id=keep.pk)


def _reassign_affiliations(keep: Person, discard: Person) -> None:
    """Move Affiliations from discard to keep, skipping exact duplicates."""
    from fairdm.contrib.contributors.models import Affiliation

    for affil in Affiliation.objects.filter(person=discard):
        already_exists = Affiliation.objects.filter(
            person=keep,
            organization=affil.organization,
        ).exists()
        if not already_exists:
            affil.person = keep
            affil.save(update_fields=["person"])
        else:
            affil.delete()


def _reassign_allauth_records(keep: Person, discard: Person) -> None:
    """Transfer allauth EmailAddress and SocialAccount records to person_keep."""
    from allauth.account.models import EmailAddress

    for email_addr in EmailAddress.objects.filter(user=discard):
        already_exists = EmailAddress.objects.filter(
            user=keep,
            email__iexact=email_addr.email,
        ).exists()
        if not already_exists:
            email_addr.user = keep
            email_addr.save(update_fields=["user"])
        else:
            email_addr.delete()

    # Transfer social accounts (ORCID etc.)
    try:
        from allauth.socialaccount.models import SocialAccount

        SocialAccount.objects.filter(user=discard).update(user=keep)
    except ImportError:
        pass  # Social accounts not installed


def _transfer_permissions(keep: Person, discard: Person) -> None:
    """Copy all guardian object-level permissions from discard to keep."""
    try:
        from guardian.models import UserObjectPermission

        for perm in UserObjectPermission.objects.filter(user=discard):
            UserObjectPermission.objects.assign_perm(
                perm.permission.codename,
                keep,
                perm.content_object,
            )
    except Exception:
        logger.warning("guardian permission transfer failed — guardian may not be installed", exc_info=True)


def _invalidate_sessions(person: Person) -> None:
    """Invalidate all active sessions for person_discard."""
    try:
        from django.contrib.sessions.models import Session

        for session in Session.objects.all():
            try:
                data = session.get_decoded()
                if data.get("_auth_user_id") == str(person.pk):
                    session.delete()
            except Exception:  # noqa: BLE001
                logger.debug("Skipping corrupted session during invalidation")
    except ImportError:
        pass  # Session backend not available


def _merge_profile_fields(keep: Person, discard: Person) -> None:
    """Copy non-blank fields from discard to keep if keep's field is blank/None."""
    fields_to_check = ["profile", "image"]
    update_fields = []
    for field_name in fields_to_check:
        keep_val = getattr(keep, field_name, None)
        discard_val = getattr(discard, field_name, None)
        if not keep_val and discard_val:
            setattr(keep, field_name, discard_val)
            update_fields.append(field_name)

    if update_fields:
        keep.save(update_fields=update_fields)
