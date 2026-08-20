"""Contributor choice enumerations.

``OrganizationType`` is drawn from ROR schema 2.1's ``types`` enumeration —
the ``items.enum`` array in ``ror-community/ror-schema/ror_schema_v2_1.json`` —
read from the schema itself rather than from documentation about it.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from research_vocabs.builder.skos import Concept
from research_vocabs.vocabularies import VocabularyBuilder

# ================== DATACITE ROLES ==================
# https://support.datacite.org/docs/schema-43-attributes#section-contributor
# https://schema.datacite.org/meta/kernel-4.3/doc/DataCite-MetadataKernel_v4.3.pdf


class OrganizationType(models.TextChoices):
    """An organisation's institutional kind, per ROR schema 2.1.

    ROR permits an organisation several types at once; this vocabulary
    deliberately narrows that to a single selection (see decisions.md D6 and
    research.md R1 in the 009-fairdm-contributors specification).
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
