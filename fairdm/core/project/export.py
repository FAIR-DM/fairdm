"""Metadata export for the Project model (US-5, FR-023 to FR-026).

Two functions map a :class:`~fairdm.core.project.models.Project` to an
external metadata form - :func:`to_datacite` for DataCite's JSON form and
:func:`to_json_ld` for schema.org JSON-LD. Both return plain dictionaries so
the administrative actions serialise the mapping rather than re-deriving it.
"""

from fairdm.core.choices import PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES

#: DataCite's own descriptionType is a closed set. "Abstract" maps straight
#: across; every other project description type maps to "Other" below and
#: carries its own type alongside so it is not lost.
_DATACITE_ABSTRACT_TYPE = "Abstract"

#: A project's own identifier vocabulary names a DOI this way (FR-025).
_DOI_IDENTIFIER_TYPE = "DOI"

#: The FairDM role that becomes a DataCite creator rather than a contributor.
_CREATOR_ROLE = "Creator"


def _datacite_contributor_type(role_name: str) -> str:
    """The DataCite ``contributorType`` for a FairDM project contribution role.

    ``PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES`` names the equivalent
    ``DataciteContributorRoles`` member by its Python attribute name (e.g.
    ``"PROJECT_LEADER"``). DataCite's own vocabulary spells that
    ``"ProjectLeader"``, so the constant name is converted directly rather
    than read off the concept's (translatable) label.
    """
    member_name = PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES.get(role_name, "OTHER")
    return "".join(part.capitalize() for part in member_name.split("_"))


def _datacite_descriptions(project) -> list:
    """Each of the project's descriptions, in DataCite's description shape."""
    entries = []
    for description in project.descriptions.all():
        if description.type == _DATACITE_ABSTRACT_TYPE:
            entries.append(
                {"description": description.value, "descriptionType": "Abstract"}
            )
        else:
            entries.append(
                {
                    "description": description.value,
                    "descriptionType": "Other",
                    "type": description.type,
                }
            )
    return entries


def _datacite_dates(project) -> list:
    """Each of the project's dates as its own entry, named via ``dateInformation``.

    DataCite has no start/end pair, and a project date's value is a
    ``PartialDate`` that may carry year, year-month or day precision -
    ``repr()`` formats it at whichever precision it carries.
    """
    return [
        {"date": repr(date.value), "dateType": "Other", "dateInformation": date.type}
        for date in project.dates.all()
    ]


def _datacite_identifiers(project) -> tuple:
    """The project's identifiers split into DataCite's primary and alternate forms.

    A DOI becomes the record's primary identifier (FR-025); every other
    identifier type becomes an alternate identifier carrying its own type.
    """
    primary = []
    alternate = []
    for identifier in project.identifiers.all():
        if identifier.type == _DOI_IDENTIFIER_TYPE:
            primary.append(
                {"identifier": identifier.value, "identifierType": _DOI_IDENTIFIER_TYPE}
            )
        else:
            alternate.append(
                {
                    "alternateIdentifier": identifier.value,
                    "alternateIdentifierType": identifier.type,
                }
            )
    return primary, alternate


def _datacite_contributions(project) -> tuple:
    """The project's contributions split into DataCite's creators and contributors.

    The ``Creator`` role becomes a creator; every other role becomes a
    contributor carrying a ``contributorType``. Each contributor's own
    representation comes from ``Contributor.to_datacite()``.
    """
    creators = []
    contributors = []
    for contribution in project.contributors.all():
        if contribution.contributor is None:
            continue
        representation = contribution.contributor.to_datacite()
        for role_name in contribution.roles.values_list("name", flat=True):
            if role_name == _CREATOR_ROLE:
                creators.append(representation)
            else:
                contributors.append(
                    {
                        **representation,
                        "contributorType": _datacite_contributor_type(role_name),
                    }
                )
    return creators, contributors


def to_datacite(project) -> dict:
    """Map ``project`` to DataCite's JSON metadata form.

    Carries the project's own fields plus its descriptions, dates,
    identifiers, contributions and funding (FR-023). Absent optional
    metadata is omitted rather than emitted as an empty structure (FR-026).
    """
    data = {
        "titles": [{"title": project.name}],
        "types": {"resourceTypeGeneral": "Project"},
    }

    if descriptions := _datacite_descriptions(project):
        data["descriptions"] = descriptions

    if dates := _datacite_dates(project):
        data["dates"] = dates

    primary_identifiers, alternate_identifiers = _datacite_identifiers(project)
    if primary_identifiers:
        data["identifiers"] = primary_identifiers
    if alternate_identifiers:
        data["alternateIdentifiers"] = alternate_identifiers

    creators, contributors = _datacite_contributions(project)
    if creators:
        data["creators"] = creators
    if contributors:
        data["contributors"] = contributors

    if project.funding:
        data["fundingReferences"] = project.funding

    return data


def to_json_ld(project) -> dict:
    """Map ``project`` to schema.org JSON-LD, carrying an explicit context (FR-024).

    Contributors come from ``Contributor.to_schema_org()``, with the
    ``email`` key dropped from each representation here - that transform is
    shared with other callers who need the address, so the key is removed
    at the export boundary rather than in the transform itself.
    """
    data = {
        "@context": {"@vocab": "https://schema.org/"},
        "@type": "ResearchProject",
        "name": project.name,
    }

    if abstract := project.descriptions.filter(type=_DATACITE_ABSTRACT_TYPE).first():
        data["description"] = abstract.value

    contributors = []
    for contribution in project.contributors.all():
        if contribution.contributor is None:
            continue
        representation = {
            key: value
            for key, value in contribution.contributor.to_schema_org().items()
            if key != "email"
        }
        contributors.append(representation)
    if contributors:
        data["contributor"] = contributors

    return data
