"""Choice enumerations and identifier lookups for contributors."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from fairdm.core.vocabularies import (
    CROSSREF_FUNDER_ID,
    DOI,
    IGSN,
    ISNI,
    ORCID,
    ROR,
    WIKIDATA,
)


class OrganizationType(models.TextChoices):
    """An organisation's institutional kind, drawn from the ``types`` enumeration of ROR schema 2.1.

    ROR permits several types at once. This vocabulary narrows that to a single selection.
    """

    EDUCATION = "education", _("Education")
    FUNDER = "funder", _("Funder")
    HEALTHCARE = "healthcare", _("Healthcare")
    COMPANY = "company", _("Company")
    ARCHIVE = "archive", _("Archive")
    NONPROFIT = "nonprofit", _("Nonprofit")
    GOVERNMENT = "government", _("Government")
    FACILITY = "facility", _("Facility")
    OTHER = "other", _("Other")


class ContributionLevel(models.IntegerChoices):
    """What a person may do on one record, each level including the ones before it.

    Stored as integers so that "at least this level" is a comparison.
    """

    VIEW = 1, _("Can view")
    EDIT = 2, _("Can edit")
    MANAGE = 3, _("Can manage")


class AccountState(models.TextChoices):
    """The four states a Person's account can be in.

    Never stored: `Person.account_state` derives one from `is_active`, `is_claimed` and
    `email`, and `PersonQuerySet` has a matching filter for each. "Inactive" takes precedence.
    """

    GHOST = "ghost", _("Ghost")
    INVITED = "invited", _("Invited")
    CLAIMED = "claimed", _("Claimed")
    INACTIVE = "inactive", _("Inactive")


# Keyed by the address of the identifier type. A type with no resolver has no entry.
IdentifierLookup = {
    ORCID: "https://orcid.org/",
    ROR: "https://ror.org/",
    WIKIDATA: "https://www.wikidata.org/wiki/",
    ISNI: "https://isni.org/isni/",
    CROSSREF_FUNDER_ID: "https://doi.org/",
    IGSN: "https://igsn.org/",
    DOI: "https://doi.org/",
}
