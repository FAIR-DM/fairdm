"""Celery tasks that sync contributors with ORCID and ROR and look for duplicates."""

import logging
from datetime import timedelta

import requests
from celery import shared_task
from django.utils import timezone
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    max_retries=3,
    rate_limit="10/m",
)
def sync_contributor_identifier(identifier_pk: int) -> bool:
    """Fetch external data for a contributor identifier and store it on the contributor.

    The ORCID or ROR API is chosen from the identifier's type.

    Args:
        identifier_pk: Primary key of the ``ContributorIdentifier``.

    Returns:
        True when the sync succeeded, False otherwise.
    """
    from .models import ContributorIdentifier

    try:
        identifier = ContributorIdentifier.objects.select_related("related").get(
            pk=identifier_pk
        )
    except ContributorIdentifier.DoesNotExist:
        logger.exception(f"ContributorIdentifier {identifier_pk} does not exist")
        return False

    contributor = identifier.related

    if identifier.type == "ORCID":
        return _sync_orcid(identifier, contributor)
    elif identifier.type == "ROR":
        return _sync_ror(identifier, contributor)
    else:
        logger.warning(f"Unknown identifier type: {identifier.type}")
        return False


def _sync_orcid(identifier, contributor):
    """Sync ORCID data for a person.

    Args:
        identifier: The ORCID identifier.
        contributor: The person it belongs to.

    Returns:
        True when the sync succeeded, False otherwise.

    Raises:
        requests.RequestException: The API request failed, so Celery retries it.
    """
    orcid_id = identifier.value
    url = f"https://pub.orcid.org/v3.0/{orcid_id}"

    try:
        response = requests.get(
            url,
            headers={"Accept": "application/json"},
            timeout=10,
        )

        if response.status_code == 404:
            logger.warning(f"ORCID {orcid_id} not found (404)")
            return False

        response.raise_for_status()
        data = response.json()

        contributor.synced_data = data
        contributor.last_synced = timezone.now().date()

        person_data = data.get("person", {})
        if person_data.get("name"):
            name_data = person_data["name"]
            given = name_data.get("given-names", {}).get("value", "")
            family = name_data.get("family-name", {}).get("value", "")
            if given and family and not contributor.name:
                contributor.name = f"{given} {family}"
                if hasattr(contributor, "first_name"):
                    contributor.first_name = given
                    contributor.last_name = family

        contributor.save()
        logger.info(f"Successfully synced ORCID {orcid_id}")

    except requests.Timeout:
        logger.exception(f"Timeout syncing ORCID {orcid_id}")
        return False
    except requests.RequestException:
        logger.exception(f"Error syncing ORCID {orcid_id}")
        raise
    except ValueError:
        logger.exception(f"Invalid JSON from ORCID API for {orcid_id}")
        return False
    except Exception:
        logger.exception(f"Unexpected error syncing ORCID {orcid_id}")
        return False
    else:
        return True


def _sync_ror(identifier, contributor):
    """Sync ROR data for an organization.

    Args:
        identifier: The ROR identifier, as a bare id or a ``ror.org`` URL.
        contributor: The organization it belongs to.

    Returns:
        True when the sync succeeded, False otherwise.

    Raises:
        requests.RequestException: The API request failed, so Celery retries it.
    """
    ror_id = identifier.value
    if "ror.org/" in ror_id:
        ror_id = ror_id.split("ror.org/")[-1]

    url = f"https://api.ror.org/organizations/{ror_id}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            logger.warning(f"ROR {ror_id} not found (404)")
            return False

        response.raise_for_status()
        data = response.json()

        contributor.synced_data = data
        contributor.last_synced = timezone.now().date()

        if data.get("addresses"):
            address = data["addresses"][0]
            if hasattr(contributor, "city") and address.get("city"):
                contributor.city = address["city"]

        if data.get("name") and not contributor.name:
            contributor.name = data["name"]

        contributor.save()
        logger.info(f"Successfully synced ROR {ror_id}")

    except requests.Timeout:
        logger.exception(f"Timeout syncing ROR {ror_id}")
        return False
    except requests.RequestException:
        logger.exception(f"Error syncing ROR {ror_id}")
        raise
    except ValueError:
        logger.exception(f"Invalid JSON from ROR API for {ror_id}")
        return False
    except Exception:
        logger.exception(f"Unexpected error syncing ROR {ror_id}")
        return False
    else:
        return True


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
        type__in=["ORCID", "ROR"],
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
