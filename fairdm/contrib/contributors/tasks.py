"""Celery tasks that sync contributors with ORCID and ROR and look for duplicates."""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone
from requests.exceptions import RequestException

from fairdm.core.vocabularies import ORCID, ROR

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(RequestException,),
    retry_backoff=True,
    max_retries=3,
    rate_limit="10/m",
)
def sync_contributor_identifier(self, identifier_pk: int) -> bool:
    """Fetch a contributor's record from ORCID or ROR and store it on the contributor.

    The registry is chosen from the identifier's type. Every fetch records its outcome on the
    contributor: a success stores the record and dates it, a failure stores why. A request
    that fails is retried with a growing delay, and a 429 after the wait the registry asks for.

    Args:
        identifier_pk: Primary key of the ``ContributorIdentifier``.

    Returns:
        True when the sync succeeded, False otherwise.

    Raises:
        requests.RequestException: The request failed, so Celery retries it.
    """
    from .models import ContributorIdentifier
    from .services.registries import RegistryRateLimited, fetch_record

    try:
        identifier = ContributorIdentifier.objects.select_related("related").get(
            pk=identifier_pk
        )
    except ContributorIdentifier.DoesNotExist:
        logger.exception(f"ContributorIdentifier {identifier_pk} does not exist")
        return False

    if identifier.type_id == ORCID:
        registry, address, headers = (
            "ORCID",
            f"https://pub.orcid.org/v3.0/{identifier.value}",
            {"Accept": "application/json"},
        )
    elif identifier.type_id == ROR:
        ror_id = identifier.value.split("ror.org/")[-1]
        registry, address, headers = (
            "ROR",
            f"https://api.ror.org/v2/organizations/{ror_id}",
            None,
        )
    else:
        logger.warning(f"Unknown identifier type: {identifier.type}")
        return False

    contributor = identifier.related.get_real_instance()
    try:
        data = fetch_record(address, headers=headers)
    except RegistryRateLimited as error:
        contributor.record_failed_fetch(
            f"{registry} asked for no requests for a while."
        )
        if error.retry_after is None:
            raise
        raise self.retry(exc=error, countdown=error.retry_after) from error
    except ValueError:
        logger.exception(f"Invalid JSON from {registry} for {identifier.value}")
        contributor.record_failed_fetch(
            f"{registry} answered in a form not understood."
        )
        return False
    except RequestException as error:
        logger.exception(f"Error syncing {registry} {identifier.value}")
        contributor.record_failed_fetch(f"{registry} request failed: {error}")
        raise

    if data is None:
        logger.warning(f"{registry} {identifier.value} not found (404)")
        contributor.record_failed_fetch(f"{registry} has no record {identifier.value}.")
        return False

    if registry == "ORCID":
        apply_orcid_record(data, contributor)
    else:
        apply_ror_record(data, contributor)
    contributor.record_fetch(data)
    contributor.save()
    logger.info(f"Successfully synced {registry} {identifier.value}")
    return True


def apply_orcid_record(data, person):
    """Fill a blank name of a person from their ORCID record, without saving.

    Args:
        data: The ORCID record.
        person: The person it belongs to.
    """
    name_data = data.get("person", {}).get("name") or {}
    given = name_data.get("given-names", {}).get("value", "")
    family = name_data.get("family-name", {}).get("value", "")
    if given and family and not person.name:
        person.name = f"{given} {family}"
        if hasattr(person, "first_name"):
            person.first_name = given
            person.last_name = family


def apply_ror_record(data, organization):
    """Set an organization's place from its ROR record, and a blank name, without saving.

    Args:
        data: The ROR record.
        organization: The organization it belongs to.
    """
    from .utils.transforms import RORTransform

    transform = RORTransform()
    transform.import_location(data, organization)
    if not organization.name:
        organization.name = transform.display_name(data)


@shared_task
def refresh_all_contributors() -> int:
    """Queue a sync for up to 100 ORCID and ROR identifiers whose contributor is unsynced or older than 7 days.

    Returns:
        The number of sync tasks queued.
    """
    from django.db.models import Q

    from .models import ContributorIdentifier

    stale_threshold = timezone.now().date() - timedelta(days=7)
    stale_identifiers = ContributorIdentifier.objects.filter(
        type_id__in=[ORCID, ROR],
    ).filter(
        Q(related__last_synced__lt=stale_threshold)
        | Q(related__last_synced__isnull=True)
    )

    count = 0
    for identifier in stale_identifiers[:100]:
        sync_contributor_identifier.delay(identifier.pk)
        count += 1

    logger.info(f"Queued {count} contributor syncs")
    return count


@shared_task
def detect_duplicate_contributors() -> dict:
    """Group people who share a lowercased, trimmed name.

    Returns:
        A dict with ``groups_found`` and ``total_duplicates``.
    """
    from .models import Person

    duplicates = {}
    persons = Person.objects.all().values("pk", "name", "email")

    for person in persons:
        normalized_name = person["name"].lower().strip()
        if normalized_name not in duplicates:
            duplicates[normalized_name] = []
        duplicates[normalized_name].append(person["pk"])

    duplicate_groups = {k: v for k, v in duplicates.items() if len(v) >= 2}

    total_duplicates = sum(len(v) for v in duplicate_groups.values())
    logger.info(
        f"Found {len(duplicate_groups)} potential duplicate groups with {total_duplicates} total persons"
    )

    return {
        "groups_found": len(duplicate_groups),
        "total_duplicates": total_duplicates,
    }
