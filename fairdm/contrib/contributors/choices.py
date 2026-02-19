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
}
