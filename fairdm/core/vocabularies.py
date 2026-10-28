"""The addresses of FairDM's vocabularies, and of the terms and collections its code names.

Each vocabulary is a SKOS concept scheme published by
`fairdm-vocabularies <https://github.com/FAIR-DM/fairdm-vocabularies>`_. A concept's address is
its vocabulary's address, a slash and the concept's identifier. A collection, the terms one kind
of record may use, sits at its vocabulary's address, a slash and the record type.
"""

from controlled_vocabularies.models import Record

#: The address every FairDM vocabulary starts with.
BASE_URI = "https://w3id.org/fairdm/vocabularies"

SAMPLE_STATUS = f"{BASE_URI}/sample-status"
DESCRIPTION_TYPES = f"{BASE_URI}/description-types"
DATE_TYPES = f"{BASE_URI}/date-types"
IDENTIFIER_TYPES = f"{BASE_URI}/identifier-types"
CONTRIBUTOR_ROLES = f"{BASE_URI}/contributor-roles"

SAMPLE_STATUS_DESTROYED = f"{SAMPLE_STATUS}/destroyed"
SAMPLE_STATUS_UNKNOWN = f"{SAMPLE_STATUS}/unknown"

ABSTRACT = f"{DESCRIPTION_TYPES}/abstract"

PROJECT_START = f"{DATE_TYPES}/start"
PROJECT_END = f"{DATE_TYPES}/end"

DOI = f"{IDENTIFIER_TYPES}/doi"
IGSN = f"{IDENTIFIER_TYPES}/igsn"
ISNI = f"{IDENTIFIER_TYPES}/isni"
ORCID = f"{IDENTIFIER_TYPES}/orcid"
ROR = f"{IDENTIFIER_TYPES}/ror"
WIKIDATA = f"{IDENTIFIER_TYPES}/wikidata"
CROSSREF_FUNDER_ID = f"{IDENTIFIER_TYPES}/crossref-funder-id"

CREATOR = f"{CONTRIBUTOR_ROLES}/creator"
CONTACT_PERSON = f"{CONTRIBUTOR_ROLES}/contact-person"
PROJECT_LEADER = f"{CONTRIBUTOR_ROLES}/project-leader"
PROJECT_MEMBER = f"{CONTRIBUTOR_ROLES}/project-member"


def collection_members(uri):
    """Return the concepts of a collection, in the order the collection lists them.

    Args:
        uri: The collection's address.

    Returns:
        A list of ``controlled_vocabularies.Record`` concepts, empty when the collection
        is not loaded.
    """
    found = Record.objects.filter(uri=uri, type__in=Record.COLLECTION_TYPES).first()
    if found is None:
        return []
    order = found.member_uris()
    by_uri = {
        concept.uri: concept
        for concept in Record.objects.filter(uri__in=order, type=Record.Type.CONCEPT)
    }
    return [by_uri[member] for member in order if member in by_uri]


def notation(concept) -> str:
    """Return the code a concept was stored as before it had an address, its ``skos:notation``.

    FairDM's own vocabularies give every concept exactly one. For the terms that DataCite also
    lists, such as the dataset description and contributor types, it is DataCite's own value.

    Args:
        concept: A ``controlled_vocabularies.Record``, or ``None``.

    Returns:
        The notation, or an empty string when there is no concept or it has none.
    """
    if concept is None:
        return ""
    return str(concept.first_value("skos:notation") or "")
