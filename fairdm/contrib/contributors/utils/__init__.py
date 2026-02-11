"""
Utilities for the contributors app.

This package provides various utility functions for working with contributors,
including API integrations, data transformations, and helper functions.
"""

# Re-export commonly used functions and classes
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

# Backward compatibility aliases for API functions
# These now delegate directly to Transform class methods
fetch_orcid_data_from_api = ORCIDTransform.fetch_from_api
fetch_ror_data_from_api = RORTransform.fetch_from_api
get_or_create_from_orcid = ORCIDTransform.get_or_create
get_or_create_from_ror = RORTransform.get_or_create
update_or_create_from_orcid = ORCIDTransform.update_or_create
update_or_create_from_ror = RORTransform.update_or_create


# Convenience functions that match expected test API
def clean_ror(ror_id_or_link: str) -> str:
    """Clean a ROR ID by extracting it from a URL if needed."""
    return RORTransform.clean_ror_id(ror_id_or_link)


def contributor_from_orcid_data(data: dict, person=None, save: bool = True):
    """Create or update a Person from ORCID API data."""
    return ORCIDTransform().import_data(data, instance=person, save=save)


def contributor_from_ror_data(data: dict, org=None, save: bool = True):
    """Create or update an Organization from ROR API data."""
    return RORTransform().import_data(data, instance=org, save=save)


__all__ = [
    # Transform classes
    "CSLJSONTransform",
    "DataCiteTransform",
    "ORCIDTransform",
    "RORTransform",
    "SchemaOrgTransform",
    # Convenience functions for working with external data
    "clean_ror",
    "contributor_from_orcid_data",
    "contributor_from_ror_data",
    "contributor_to_csljson",
    "contributor_to_datacite",
    "contributor_to_schema_org",
    "csljson_to_contributor",
    # Helper functions
    "current_user_has_role",
    # API functions (delegated to Transform classes)
    "fetch_orcid_data_from_api",
    "fetch_ror_data_from_api",
    "get_contributor_avatar",
    "get_or_create_from_orcid",
    "get_or_create_from_ror",
    "update_or_create_contribution",
    "update_or_create_from_orcid",
    "update_or_create_from_ror",
]
