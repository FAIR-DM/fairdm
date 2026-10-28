"""Metadata export for the Project model.

:class:`ProjectDataCiteTransform` maps a project to DataCite's JSON form and
:class:`ProjectSchemaOrgTransform` to schema.org JSON-LD. The module-level
:func:`to_datacite` and :func:`to_json_ld` wrap them for the administrative actions.
"""

from fairdm.contrib.contributors.utils.transforms import BaseTransform
from fairdm.core.vocabularies import ABSTRACT, CREATOR, DOI, notation

# Each type and role is written as its concept's notation, which for every project role is
# DataCite's own contributorType. DataCite's descriptionType is a closed set: the abstract maps
# straight across, and every other project description type maps to "Other" and carries its own
# type alongside so it is not lost.


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

    def _descriptions(self, project) -> list:
        """Return each of the project's descriptions in DataCite's description shape."""
        entries = []
        for description in project.descriptions.all():
            if description.type_id == ABSTRACT:
                entries.append(
                    {"description": description.value, "descriptionType": "Abstract"}
                )
            else:
                entries.append(
                    {
                        "description": description.value,
                        "descriptionType": "Other",
                        "type": notation(description.type),
                    }
                )
        return entries

    def _dates(self, project) -> list:
        """Return each of the project's dates as its own entry, named via ``dateInformation``.

        DataCite has no start/end pair. ``str()`` formats a ``PartialDate`` at its own precision.
        """
        return [
            {
                "date": str(date.value),
                "dateType": "Other",
                "dateInformation": notation(date.type),
            }
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
            if identifier.type_id == DOI:
                primary.append(
                    {
                        "identifier": identifier.value,
                        "identifierType": notation(identifier.type),
                    }
                )
            else:
                alternate.append(
                    {
                        "alternateIdentifier": identifier.value,
                        "alternateIdentifierType": notation(identifier.type),
                    }
                )
        return primary, alternate

    def _contributions(self, project) -> tuple:
        """Split the project's contributions into DataCite's creators and contributors.

        The creator role becomes a creator. Every other role becomes a contributor carrying its
        notation as the ``contributorType``.
        """
        creators = []
        contributors = []
        for contribution in project.contributors.all():
            if contribution.contributor is None:
                continue
            representation = contribution.contributor.to_datacite()
            # `.all()` reads the prefetch cache; `.values_list()` would query per contribution.
            for role in contribution.roles.all():
                if role.uri == CREATOR:
                    creators.append(representation)
                else:
                    contributors.append(
                        {**representation, "contributorType": notation(role)}
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
                if description.type_id == ABSTRACT
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
