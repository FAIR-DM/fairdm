"""Tests for the DataCite and JSON-LD exports in ``fairdm.core.project.transforms``."""

import pytest

from fairdm.core.project.transforms import to_datacite, to_json_ld
from fairdm.factories import (
    PersonFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
)
from fairdm.factories.core import ProjectDateFactory


@pytest.mark.django_db
class TestToDatacite:
    def test_fully_populated_project_carries_every_related_record(self):
        project = ProjectFactory(
            funding=[{"funderName": "Sample Agency", "awardNumber": "GRANT-42"}]
        )
        ProjectDescriptionFactory(
            related=project, type="Abstract", value="An abstract."
        )
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

        assert data["titles"] == [{"title": project.name}]

        assert {
            "description": "An abstract.",
            "descriptionType": "Abstract",
        } in data["descriptions"]
        assert {
            "description": "Do the thing.",
            "descriptionType": "Other",
            "type": "Objectives",
        } in data["descriptions"]

        dates_by_information = {d["dateInformation"]: d["date"] for d in data["dates"]}
        assert dates_by_information == {"Start": "2024-01-01", "End": "2024-12"}

        assert data["identifiers"] == [
            {"identifier": "10.1234/example-project", "identifierType": "DOI"}
        ]
        assert data["alternateIdentifiers"] == [
            {
                "alternateIdentifier": "PROP-2024-01",
                "alternateIdentifierType": "PROPOSAL_ID",
            }
        ]

        assert len(data["creators"]) == 1
        assert data["creators"][0]["name"] == creator.name
        assert len(data["contributors"]) == 1
        assert data["contributors"][0]["name"] == member.name
        assert data["contributors"][0]["contributorType"] == "ProjectMember"

        assert data["fundingReferences"] == project.funding

    def test_funding_references_is_not_the_same_list_as_the_model_field(self):
        project = ProjectFactory(
            funding=[{"funderName": "Sample Agency", "awardNumber": "GRANT-42"}]
        )

        data = to_datacite(project)
        data["fundingReferences"].append({"funderName": "Injected Agency"})

        assert len(project.funding) == 1
        assert project.funding[0]["funderName"] == "Sample Agency"

    def test_doi_becomes_the_records_primary_identifier(self):
        project = ProjectFactory(funding=None)
        ProjectIdentifierFactory(
            related=project, type="DOI", value="10.5555/primary-example"
        )
        ProjectIdentifierFactory(related=project, type="GRANT_NUMBER", value="GRANT-99")

        data = to_datacite(project)

        assert data["identifiers"] == [
            {"identifier": "10.5555/primary-example", "identifierType": "DOI"}
        ]
        assert all(
            entry["alternateIdentifier"] != "10.5555/primary-example"
            for entry in data["alternateIdentifiers"]
        )

    def test_minimally_populated_project_omits_absent_parts(self):
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
    def test_output_parses_as_json_ld_with_context(self):
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
        project = ProjectFactory(funding=None)
        person = PersonFactory(email="contributor@example.org")
        project.add_contributor(person, with_roles=["ProjectMember"])

        data = to_json_ld(project)

        assert data["contributor"]
        for representation in data["contributor"]:
            assert "email" not in representation
