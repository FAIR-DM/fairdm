"""Metadata export for the Project model.

:class:`ProjectDataCiteTransform` maps a project to DataCite's JSON form and
:class:`ProjectSchemaOrgTransform` to schema.org JSON-LD. The module-level
:func:`to_datacite` and :func:`to_json_ld` wrap them for the administrative actions.
"""

from fairdm.contrib.contributors.utils.transforms import BaseTransform
from fairdm.core.choices import PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES

#: DataCite's own descriptionType is a closed set. "Abstract" maps straight
#: across; every other project description type maps to "Other" below and
#: carries its own type alongside so it is not lost.
_DATACITE_ABSTRACT_TYPE = "Abstract"

#: A project's own identifier vocabulary names a DOI this way.
_DOI_IDENTIFIER_TYPE = "DOI"

#: The FairDM role that becomes a DataCite creator rather than a contributor.
_CREATOR_ROLE = "Creator"


class ProjectDataCiteTransform(BaseTransform):
    """Map a project to DataCite's JSON metadata form.

    ``BaseTransform.export()`` is typed on ``Contributor``, and generalising it is out of scope
    (#176), so this override narrows the parameter type instead.
    """

    def export(self, project) -> dict:
        """Map a project to DataCite's JSON metadata form.

        Carries the project's name plus its descriptions, dates, identifiers, contributions and
        funding. Absent optional metadata is omitted rather than emitted as an empty structure.

        Args:
            project: The project to export.

        Returns:
            The DataCite metadata dictionary.
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
            # A copy, so a caller mutating the result does not mutate `project.funding`.
            data["fundingReferences"] = list(project.funding)

        return data

    def _contributor_type(self, role_name: str) -> str:
        """Return the DataCite ``contributorType`` for a project contribution role.

        The equivalent member is named by its Python attribute (``"PROJECT_LEADER"``), which is
        converted to DataCite's spelling (``"ProjectLeader"``) rather than read off the
        translatable label.
        """
        member_name = PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES.get(role_name, "OTHER")
        return "".join(part.capitalize() for part in member_name.split("_"))

    def _descriptions(self, project) -> list:
        """Return each of the project's descriptions in DataCite's description shape."""
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
        """Return each of the project's dates as its own entry, named via ``dateInformation``.

        DataCite has no start/end pair. ``str()`` formats a ``PartialDate`` at its own precision.
        """
        return [
            {"date": str(date.value), "dateType": "Other", "dateInformation": date.type}
            for date in project.dates.all()
        ]

    def _identifiers(self, project) -> tuple:
        """Split the project's identifiers into DataCite's primary and alternate forms.

        A DOI becomes the primary identifier. Every other type becomes an alternate identifier
        carrying its own type.
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
        """Split the project's contributions into DataCite's creators and contributors.

        The ``Creator`` role becomes a creator. Every other role becomes a contributor carrying a
        ``contributorType``.
        """
        creators = []
        contributors = []
        for contribution in project.contributors.all():
            if contribution.contributor is None:
                continue
            representation = contribution.contributor.to_datacite()
            # `.all()` reads the prefetch cache; `.values_list()` would query per contribution.
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
    """Map a project to schema.org JSON-LD.

    ``BaseTransform.export()`` is typed on ``Contributor``, and generalising it is out of scope
    (#176), so this override narrows the parameter type instead.
    """

    def export(self, project) -> dict:
        """Map a project to schema.org JSON-LD, carrying an explicit context.

        The ``email`` key is dropped from each contributor here. The contributor transform is
        shared with callers who need the address, so it is removed at the export boundary.

        Args:
            project: The project to export.

        Returns:
            The JSON-LD dictionary.
        """
        data = {
            "@context": {"@vocab": "https://schema.org/"},
            "@type": "ResearchProject",
            "name": project.name,
        }

        # `.all()` reads the prefetch cache; `.filter()` would always query.
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
    """Map a project to DataCite's JSON metadata form.

    Args:
        project: The project to export.

    Returns:
        The DataCite metadata dictionary.
    """
    return ProjectDataCiteTransform().export(project)


def to_json_ld(project) -> dict:
    """Map a project to schema.org JSON-LD.

    Args:
        project: The project to export.

    Returns:
        The JSON-LD dictionary.
    """
    return ProjectSchemaOrgTransform().export(project)
