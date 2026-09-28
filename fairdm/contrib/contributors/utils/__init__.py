"""Utilities for contributors: external-data transforms, helpers and tokens."""

from .helpers import (
    current_user_has_role,
    get_contributor_avatar,
    update_or_create_contribution,
)
from .transforms import (
    CSLJSONTransform,
    DataCiteTransform,
    ORCIDTransform,
    RORTransform,
    SchemaOrgTransform,
    contributor_to_csljson,
    contributor_to_datacite,
    contributor_to_schema_org,
    csljson_to_contributor,
)

fetch_orcid_data_from_api = ORCIDTransform.fetch_from_api
fetch_ror_data_from_api = RORTransform.fetch_from_api
get_or_create_from_orcid = ORCIDTransform.get_or_create
get_or_create_from_ror = RORTransform.get_or_create
update_or_create_from_orcid = ORCIDTransform.update_or_create
update_or_create_from_ror = RORTransform.update_or_create


def clean_ror(ror_id_or_link: str) -> str:
    """Extract a bare ROR id from an id or a ``ror.org`` URL.

    Args:
        ror_id_or_link: A ROR id or URL.

    Returns:
        The bare ROR id.
    """
    return RORTransform.clean_ror_id(ror_id_or_link)


def contributor_from_orcid_data(data: dict, person=None, save: bool = True):
    """Create or update a person from ORCID API data.

    Args:
        data: The ORCID API record.
        person: An existing person to update.
        save: Whether to save the result.

    Returns:
        The person.
    """
    return ORCIDTransform().import_data(data, instance=person, save=save)


def contributor_from_ror_data(data: dict, org=None, save: bool = True):
    """Create or update an organisation from ROR API data.

    Args:
        data: The ROR API record.
        org: An existing organisation to update.
        save: Whether to save the result.

    Returns:
        The organisation.
    """
    return RORTransform().import_data(data, instance=org, save=save)


__all__ = [
    "CSLJSONTransform",
    "DataCiteTransform",
    "ORCIDTransform",
    "RORTransform",
    "SchemaOrgTransform",
    "clean_ror",
    "contributor_from_orcid_data",
    "contributor_from_ror_data",
    "contributor_to_csljson",
    "contributor_to_datacite",
    "contributor_to_schema_org",
    "csljson_to_contributor",
    "current_user_has_role",
    "fetch_orcid_data_from_api",
    "fetch_ror_data_from_api",
    "get_contributor_avatar",
    "get_or_create_from_orcid",
    "get_or_create_from_ror",
    "update_or_create_contribution",
    "update_or_create_from_orcid",
    "update_or_create_from_ror",
]
