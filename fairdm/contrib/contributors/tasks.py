"""Celery tasks for contributor synchronization.

Tasks:
- sync_contributor_identifier: Fetch ORCID/ROR data for a ContributorIdentifier
- refresh_all_contributors: Periodic task to refresh stale data
- detect_duplicate_contributors: Periodic task to find potential duplicates
"""

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
    """Fetch external data for a ContributorIdentifier.

    Determines API (ORCID/ROR) from identifier type.
    Updates Contributor.synced_data and last_synced.

    Args:
        identifier_pk: Primary key of ContributorIdentifier instance.

    Returns:
        bool: True if sync succeeded, False otherwise.
    """
    from .models import ContributorIdentifier

    try:
        identifier = ContributorIdentifier.objects.select_related("related").get(pk=identifier_pk)
    except ContributorIdentifier.DoesNotExist:
        logger.exception(f"ContributorIdentifier {identifier_pk} does not exist")
        return False

    contributor = identifier.related

    # Dispatch to appropriate sync function based on identifier type
    if identifier.type == "ORCID":
        return _sync_orcid(identifier, contributor)
    elif identifier.type == "ROR":
        return _sync_ror(identifier, contributor)
    else:
        logger.warning(f"Unknown identifier type: {identifier.type}")
        return False


def _sync_orcid(identifier, contributor):
    """Sync ORCID data for a person."""
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

        # Update contributor with synced data
        contributor.synced_data = data
        contributor.last_synced = timezone.now().date()

        # Extract name if available and contributor name is empty
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
        return True

    except requests.Timeout:
        logger.exception(f"Timeout syncing ORCID {orcid_id}")
        return False
    except requests.RequestException as e:
        logger.exception(f"Error syncing ORCID {orcid_id}: {e}")
        raise  # Let Celery retry
    except ValueError as e:
        logger.exception(f"Invalid JSON from ORCID API for {orcid_id}: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error syncing ORCID {orcid_id}: {e}")
        return False


def _sync_ror(identifier, contributor):
    """Sync ROR data for an organization."""
    ror_id = identifier.value
    # Extract ROR ID from URL if needed
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

        # Update organization with synced data
        contributor.synced_data = data
        contributor.last_synced = timezone.now().date()

        # Extract location if available
        if data.get("addresses"):
            address = data["addresses"][0]
            if hasattr(contributor, "city") and address.get("city"):
                contributor.city = address["city"]

        # Extract name
        if data.get("name") and not contributor.name:
            contributor.name = data["name"]

        contributor.save()
        logger.info(f"Successfully synced ROR {ror_id}")
        return True

    except requests.Timeout:
        logger.exception(f"Timeout syncing ROR {ror_id}")
        return False
    except requests.RequestException as e:
        logger.exception(f"Error syncing ROR {ror_id}: {e}")
        raise  # Let Celery retry
    except ValueError as e:
        logger.exception(f"Invalid JSON from ROR API for {ror_id}: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error syncing ROR {ror_id}: {e}")
        return False


@shared_task
def refresh_all_contributors() -> int:
    """Periodic task: refresh stale contributors.

    Queries contributors where last_synced is older than 7 days or NULL.
    Processes in batches with delays to respect rate limits.

    Returns:
        int: Number of sync tasks queued.
    """
    from django.db.models import Q

    from .models import ContributorIdentifier

    # Find identifiers that need refreshing
    stale_threshold = timezone.now().date() - timedelta(days=7)
    stale_identifiers = ContributorIdentifier.objects.filter(
        type__in=["ORCID", "ROR"],
    ).filter(Q(related__last_synced__lt=stale_threshold) | Q(related__last_synced__isnull=True))

    count = 0
    for identifier in stale_identifiers[:100]:  # Limit to 100 per run
        sync_contributor_identifier.delay(identifier.pk)
        count += 1

    logger.info(f"Queued {count} contributor syncs")
    return count


@shared_task
def detect_duplicate_contributors() -> dict:
    """Periodic task: identify potential duplicate contributor profiles.

    Uses name similarity and identifier matching to find duplicates.

    Returns:
        dict: {"groups_found": N, "total_duplicates": N}
    """
    from .models import Person

    # Simple duplicate detection: find persons with same normalized name
    # More sophisticated matching would use fuzzy string matching
    duplicates = {}
    persons = Person.objects.all().values("pk", "name", "email")

    for person in persons:
        normalized_name = person["name"].lower().strip()
        if normalized_name not in duplicates:
            duplicates[normalized_name] = []
        duplicates[normalized_name].append(person["pk"])

    # Filter to groups with 2+ members
    duplicate_groups = {k: v for k, v in duplicates.items() if len(v) >= 2}

    total_duplicates = sum(len(v) for v in duplicate_groups.values())
    logger.info(f"Found {len(duplicate_groups)} potential duplicate groups with {total_duplicates} total persons")

    return {
        "groups_found": len(duplicate_groups),
        "total_duplicates": total_duplicates,
    }
