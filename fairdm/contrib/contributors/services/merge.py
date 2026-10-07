"""Person merge service that moves one person's data to another and deletes the first."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.db import transaction

from fairdm.contrib.contributors.exceptions import ClaimingError

if TYPE_CHECKING:
    from fairdm.contrib.contributors.models import Person

logger = logging.getLogger(__name__)


def merge_persons(person_keep: Person, person_discard: Person) -> Person:
    """Merge ``person_discard`` into ``person_keep`` in one atomic transaction.

    The kept person receives the discarded person's unique contributions, identifiers,
    affiliations, email addresses and stored permissions on other objects, is marked claimed
    and active, and the discarded person is deleted. Stored permissions on projects, datasets,
    samples and measurements are not copied, because levels move with the contributions. Any
    error rolls the whole merge back.

    Args:
        person_keep: The person that survives.
        person_discard: The person that is deleted.

    Returns:
        The updated ``person_keep``.

    Raises:
        ClaimingError: Both arguments are the same person.
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

        person_keep.is_claimed = True
        person_keep.is_active = True
        person_keep.save(update_fields=["is_claimed", "is_active"])

        person_discard.delete()

    return person_keep


def _reassign_contributions(keep: Person, discard: Person) -> None:
    """Move Contributions from discard to keep, keeping the higher level where both are listed.

    A record both people are listed on keeps the kept person's entry, with its organization as
    it is, at the higher of the two levels. The discarded person's entry there is dropped.
    """
    from fairdm.contrib.contributors.models import Contribution

    for contrib in Contribution.objects.filter(contributor=discard):
        kept = Contribution.objects.filter(
            contributor=keep,
            content_type=contrib.content_type,
            object_id=contrib.object_id,
        ).first()
        if kept is None:
            contrib.contributor = keep
            contrib.save(update_fields=["contributor"])
            continue
        if contrib.level is not None and (
            kept.level is None or contrib.level > kept.level
        ):
            kept.level = contrib.level
            kept.save(update_fields=["level"])
        contrib.delete()


def _reassign_identifiers(keep: Person, discard: Person) -> None:
    """Move ContributorIdentifiers from discard to keep, avoiding constraint violations."""
    from fairdm.contrib.contributors.models import ContributorIdentifier

    for identifier in ContributorIdentifier.objects.filter(related=discard):
        # `value` is globally unique, and a contributor holds one identifier per type.
        value_exists = (
            ContributorIdentifier.objects.filter(value=identifier.value)
            .exclude(pk=identifier.pk)
            .exists()
        )
        type_exists_on_keep = ContributorIdentifier.objects.filter(
            related=keep, type=identifier.type
        ).exists()

        if value_exists or type_exists_on_keep:
            identifier.delete()
        else:
            # `update()` skips the AFTER_CREATE hook that would queue a sync task.
            ContributorIdentifier.objects.filter(pk=identifier.pk).update(
                related_id=keep.pk
            )


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

    try:
        from allauth.socialaccount.models import SocialAccount

        SocialAccount.objects.filter(user=discard).update(user=keep)
    except ImportError:
        pass


def _transfer_permissions(keep: Person, discard: Person) -> None:
    """Copy guardian object-level permissions from discard to keep, except on core records.

    A stored row grants nothing on a project, dataset, sample or measurement: what a person may
    do there is the level of their contribution, which ``_reassign_contributions`` carries over.
    """
    try:
        from guardian.models import UserObjectPermission

        from fairdm.contrib.contributors.access import RecordAccess

        for perm in UserObjectPermission.objects.filter(user=discard):
            if RecordAccess.is_core_record(perm.content_object):
                continue
            UserObjectPermission.objects.assign_perm(
                perm.permission.codename,
                keep,
                perm.content_object,
            )
    except Exception:
        logger.warning(
            "guardian permission transfer failed — guardian may not be installed",
            exc_info=True,
        )


def _invalidate_sessions(person: Person) -> None:
    """Invalidate all active sessions for person_discard."""
    try:
        from django.contrib.sessions.models import Session

        for session in Session.objects.all():
            try:
                data = session.get_decoded()
                if data.get("_auth_user_id") == str(person.pk):
                    session.delete()
            except Exception:
                logger.debug("Skipping corrupted session during invalidation")
    except ImportError:
        pass


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
