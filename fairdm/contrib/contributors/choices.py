from django.db import models
from django.utils.translation import gettext_lazy as _
from research_vocabs.builder.skos import Concept
from research_vocabs.vocabularies import VocabularyBuilder

# ================== DATACITE ROLES ==================
# https://support.datacite.org/docs/schema-43-attributes#section-contributor
# https://schema.datacite.org/meta/kernel-4.3/doc/DataCite-MetadataKernel_v4.3.pdf


class DefaultGroups(models.TextChoices):
    """Default groups for contributors."""

    PORTAL_ADMIN = "Portal Administrators", _("Portal Administrators")
    DATA_ADMIN = "Data Administrators", _("Data Administrators")
    DEVELOPERS = "Developers", _("Developers")


class PersonalIdentifiers(models.TextChoices):
    ORCID = "ORCID", "ORCID"
    RESEARCHER_ID = "ResearcherID", "ResearcherID"


class OrganizationalIdentifiers(models.TextChoices):
    ROR = "ROR", "ROR"
    GRID = "GRID", "GRID"
    WIKIDATA = "Wikidata", "Wikidata"
    ISNI = "ISNI", "ISNI"
    CROSSREF_FUNDER_ID = "Crossref Funder ID", "Crossref Funder ID"


class AccountState(models.TextChoices):
    """The four states a Person's account can be in (decisions.md D8).

    Never stored: `Person.account_state` derives one of these members from
    `is_active`, `is_claimed` and `email`, and `PersonQuerySet` carries a
    matching filter for each. "Inactive" takes precedence over every other
    signal, "banned" having been reworded to describe what the flag means.
    """

    GHOST = "ghost", _("Ghost")
    INVITED = "invited", _("Invited")
    CLAIMED = "claimed", _("Claimed")
    INACTIVE = "inactive", _("Inactive")


class FairDMIdentifiers(VocabularyBuilder):
    ORCID = Concept(
        prefLabel=_("ORCID"),
        definition=_("Open Researcher and Contributor ID."),
    )


IdentifierLookup = {
    "ORCID": "https://orcid.org/",
    "ROR": "https://ror.org/",
    "GRID": "https://www.grid.ac/institutes/",
    "Wikidata": "https://www.wikidata.org/wiki/",
    "ISNI": "https://isni.org/isni/",
    "Crossref Funder ID": "https://doi.org/",
    "IGSN": "https://igsn.org/",
    "DOI": "https://doi.org/",
}
