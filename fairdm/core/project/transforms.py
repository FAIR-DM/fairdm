"""Metadata export for the Project model (US-5, FR-023 to FR-026).

Two transform classes map a :class:`~fairdm.core.project.models.Project` to
an external metadata form, mirroring the shape of
:mod:`fairdm.contrib.contributors.utils.transforms` one model up:
:class:`ProjectDataCiteTransform` for DataCite's JSON form and
:class:`ProjectSchemaOrgTransform` for schema.org JSON-LD. The module-level
:func:`to_datacite` and :func:`to_json_ld` are thin convenience wrappers, the
same way :func:`contributor_to_datacite` wraps :class:`DataCiteTransform` at
the bottom of that module - the administrative actions call these rather
than re-deriving the mapping.
"""

from fairdm.contrib.contributors.utils.transforms import BaseTransform
from fairdm.core.choices import PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES

#: DataCite's own descriptionType is a closed set. "Abstract" maps straight
#: across; every other project description type maps to "Other" below and
#: carries its own type alongside so it is not lost.
_DATACITE_ABSTRACT_TYPE = "Abstract"

#: A project's own identifier vocabulary names a DOI this way (FR-025).
_DOI_IDENTIFIER_TYPE = "DOI"

#: The FairDM role that becomes a DataCite creator rather than a contributor.
_CREATOR_ROLE = "Creator"


class ProjectDataCiteTransform(BaseTransform):
    """Maps a Project to DataCite's JSON metadata form (FR-023).

    `BaseTransform.export()` is typed on `Contributor`. Generalising it to
    cover a project too is filed separately as issue #176 and is out of
    scope here, so this override narrows the parameter type instead of
    widening the base class's.
    """

    def export(self, project) -> dict:
        """Map ``project`` to DataCite's JSON metadata form.

        Carries the project's own fields plus its descriptions, dates,
        identifiers, contributions and funding (FR-023). Absent optional
        metadata is omitted rather than emitted as an empty structure
        (FR-026).
        """
        data = {
            "titles": [{"title": project.name}],
            "types": {"resourceTypeGeneral": "Project"},
        }

        if descriptions := self._descriptions(project):
            data["descriptions"] = descriptions

        if dates := self._dates(project):
            data["dates"] = dates

        primary_identifiers, alternate_identifiers = self._identifiers(project)
        if primary_identifiers:
            data["identifiers"] = primary_identifiers
        if alternate_identifiers:
            data["alternateIdentifiers"] = alternate_identifiers

        creators, contributors = self._contributions(project)
        if creators:
            data["creators"] = creators
        if contributors:
            data["contributors"] = contributors

        if project.funding:
            # A shallow copy - a caller mutating the returned list must not
            # mutate `project.funding` in memory.
            data["fundingReferences"] = list(project.funding)

        return data

    def _contributor_type(self, role_name: str) -> str:
        """The DataCite ``contributorType`` for a FairDM project contribution role.

        ``PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES`` names the equivalent
        ``DataciteContributorRoles`` member by its Python attribute name
        (e.g. ``"PROJECT_LEADER"``). DataCite's own vocabulary spells that
        ``"ProjectLeader"``, so the constant name is converted directly
        rather than read off the concept's (translatable) label.
        """
        member_name = PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES.get(role_name, "OTHER")
        return "".join(part.capitalize() for part in member_name.split("_"))

    def _descriptions(self, project) -> list:
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

    def _dates(self, project) -> list:
        """Each of the project's dates as its own entry, named via ``dateInformation``.

        DataCite has no start/end pair, and a project date's value is a
        ``PartialDate`` that may carry year, year-month or day precision -
        ``str()`` formats it at whichever precision it carries.
        """
        return [
            {"date": str(date.value), "dateType": "Other", "dateInformation": date.type}
            for date in project.dates.all()
        ]

    def _identifiers(self, project) -> tuple:
        """The project's identifiers split into DataCite's primary and alternate forms.

        A DOI becomes the record's primary identifier (FR-025); every other
        identifier type becomes an alternate identifier carrying its own
        type.
        """
        primary = []
        alternate = []
        for identifier in project.identifiers.all():
            if identifier.type == _DOI_IDENTIFIER_TYPE:
                primary.append(
                    {
                        "identifier": identifier.value,
                        "identifierType": _DOI_IDENTIFIER_TYPE,
                    }
                )
            else:
                alternate.append(
                    {
                        "alternateIdentifier": identifier.value,
                        "alternateIdentifierType": identifier.type,
                    }
                )
        return primary, alternate

    def _contributions(self, project) -> tuple:
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
            # `.all()` rather than `.values_list()` - the latter always
            # issues its own query, bypassing a
            # `prefetch_related("contributors__roles")` the caller may have
            # applied to avoid a query per contribution.
            for role_name in (role.name for role in contribution.roles.all()):
                if role_name == _CREATOR_ROLE:
                    creators.append(representation)
                else:
                    contributors.append(
                        {
                            **representation,
                            "contributorType": self._contributor_type(role_name),
                        }
                    )
        return creators, contributors


class ProjectSchemaOrgTransform(BaseTransform):
    """Maps a Project to schema.org JSON-LD (FR-024).

    `BaseTransform.export()` is typed on `Contributor`. Generalising it to
    cover a project too is filed separately as issue #176 and is out of
    scope here, so this override narrows the parameter type instead of
    widening the base class's.
    """

    def export(self, project) -> dict:
        """Map ``project`` to schema.org JSON-LD, carrying an explicit context (FR-024).

        Contributors come from ``Contributor.to_schema_org()``, with the
        ``email`` key dropped from each representation here - that
        transform is shared with other callers who need the address, so the
        key is removed at the export boundary rather than in the transform
        itself.
        """
        data = {
            "@context": {"@vocab": "https://schema.org/"},
            "@type": "ResearchProject",
            "name": project.name,
        }

        # `.all()` rather than `.filter()` - the latter always issues its
        # own query, bypassing a `prefetch_related("descriptions")` the
        # caller may have applied.
        abstract = next(
            (
                description
                for description in project.descriptions.all()
                if description.type == _DATACITE_ABSTRACT_TYPE
            ),
            None,
        )
        if abstract:
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


def to_datacite(project) -> dict:
    """Map ``project`` to DataCite's JSON metadata form."""
    return ProjectDataCiteTransform().export(project)


def to_json_ld(project) -> dict:
    """Map ``project`` to schema.org JSON-LD."""
    return ProjectSchemaOrgTransform().export(project)
