"""Tests for fairdm/core/project/export.py (US-5: metadata export).

Covers FR-023 to FR-026: DataCite JSON export, JSON-LD export, the DOI as
primary identifier, and omitting absent optional metadata.
"""

import pytest

from fairdm.core.project.export import to_datacite, to_json_ld
from fairdm.factories import (
    PersonFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
)
from fairdm.factories.core import ProjectDateFactory


@pytest.mark.django_db
class TestToDatacite:
    """`to_datacite(project)` maps a project to DataCite's JSON form (FR-023)."""

    def test_fully_populated_project_carries_every_related_record(self):
        """T040: every kind of related record appears in the DataCite output."""
        project = ProjectFactory(
            funding=[{"funderName": "Sample Agency", "awardNumber": "GRANT-42"}]
        )
        ProjectDescriptionFactory(related=project, type="Abstract", value="An abstract.")
        ProjectDescriptionFactory(
            related=project, type="Objectives", value="Do the thing."
        )
        ProjectDateFactory(related=project, type="Start", value="2024-01-01")
        ProjectDateFactory(related=project, type="End", value="2024-12")
        ProjectIdentifierFactory(
            related=project, type="DOI", value="10.1234/example-project"
        )
        ProjectIdentifierFactory(
            related=project, type="PROPOSAL_ID", value="PROP-2024-01"
        )
        creator = PersonFactory()
        member = PersonFactory()
        project.add_contributor(creator, with_roles=["Creator"])
        project.add_contributor(member, with_roles=["ProjectMember"])

        data = to_datacite(project)

        # Own fields
        assert data["titles"] == [{"title": project.name}]

        # Descriptions - Abstract maps straight across, Objectives maps to
        # Other but keeps its own type alongside.
        assert {
            "description": "An abstract.",
            "descriptionType": "Abstract",
        } in data["descriptions"]
        assert {
            "description": "Do the thing.",
            "descriptionType": "Other",
            "type": "Objectives",
        } in data["descriptions"]

        # Dates - one entry per type, named via dateInformation.
        dates_by_information = {d["dateInformation"]: d["date"] for d in data["dates"]}
        assert dates_by_information == {"Start": "2024-01-01", "End": "2024-12"}

        # Identifiers - DOI primary, everything else alternate.
        assert data["identifiers"] == [
            {"identifier": "10.1234/example-project", "identifierType": "DOI"}
        ]
        assert data["alternateIdentifiers"] == [
            {
                "alternateIdentifier": "PROP-2024-01",
                "alternateIdentifierType": "PROPOSAL_ID",
            }
        ]

        # Contributions - Creator role becomes a creator, everything else a
        # contributor carrying a contributorType.
        assert len(data["creators"]) == 1
        assert data["creators"][0]["name"] == creator.name
        assert len(data["contributors"]) == 1
        assert data["contributors"][0]["name"] == member.name
        assert data["contributors"][0]["contributorType"] == "ProjectMember"

        # Funding passes through unchanged.
        assert data["fundingReferences"] == project.funding

    def test_doi_becomes_the_records_primary_identifier(self):
        """T041: a DOI is the primary identifier, not one alternate among others."""
        project = ProjectFactory(funding=None)
        ProjectIdentifierFactory(
            related=project, type="DOI", value="10.5555/primary-example"
        )
        ProjectIdentifierFactory(
            related=project, type="GRANT_NUMBER", value="GRANT-99"
        )

        data = to_datacite(project)

        assert data["identifiers"] == [
            {"identifier": "10.5555/primary-example", "identifierType": "DOI"}
        ]
        assert all(
            entry["alternateIdentifier"] != "10.5555/primary-example"
            for entry in data["alternateIdentifiers"]
        )

    def test_minimally_populated_project_omits_absent_parts(self):
        """T042: a minimal project exports successfully with no empty structures."""
        project = ProjectFactory(funding=None)

        data = to_datacite(project)

        assert data["titles"] == [{"title": project.name}]
        for key in (
            "descriptions",
            "dates",
            "identifiers",
            "alternateIdentifiers",
            "creators",
            "contributors",
            "fundingReferences",
        ):
            assert key not in data


@pytest.mark.django_db
class TestToJsonLd:
    """`to_json_ld(project)` maps a project to schema.org JSON-LD (FR-024)."""

    def test_output_parses_as_json_ld_with_context(self):
        """T044: the output parses as JSON-LD and carries an explicit context."""
        import json

        from rdflib import Graph

        project = ProjectFactory(name="A Research Project", funding=None)

        data = to_json_ld(project)

        assert "@context" in data
        assert data["@type"] == "ResearchProject"

        graph = Graph()
        graph.parse(data=json.dumps(data), format="json-ld")
        assert len(graph) > 0

    def test_contributor_email_is_dropped_from_the_export(self):
        """Security requirement: a contributor's email never leaves in the export.

        `Contributor.to_schema_org()` includes the email address wherever
        one is recorded - that transform is shared with other callers, so
        the key is dropped here rather than in the transform itself.
        """
        project = ProjectFactory(funding=None)
        person = PersonFactory(email="contributor@example.org")
        project.add_contributor(person, with_roles=["ProjectMember"])

        data = to_json_ld(project)

        assert data["contributor"]
        for representation in data["contributor"]:
            assert "email" not in representation
