"""Tests for the contributor data transforms."""

import pytest

from fairdm.contrib.contributors.models import Organization
from fairdm.contrib.contributors.utils.transforms import (
    CSLJSONTransform,
    DataCiteTransform,
    ORCIDTransform,
    RORTransform,
    SchemaOrgTransform,
)


@pytest.mark.django_db
class TestDataCitePersonExport:
    def test_datacite_export_person_basic(self, person):
        transform = DataCiteTransform()
        datacite_data = transform.export(person)

        assert "name" in datacite_data
        assert datacite_data["name"] == person.name
        assert "nameType" in datacite_data
        assert datacite_data["nameType"] == "Personal"

    def test_datacite_export_person_with_orcid(self, person, orcid_identifier):
        transform = DataCiteTransform()
        datacite_data = transform.export(person)

        assert "nameIdentifiers" in datacite_data
        assert len(datacite_data["nameIdentifiers"]) > 0
        orcid_id = datacite_data["nameIdentifiers"][0]
        assert orcid_id["nameIdentifier"] == orcid_identifier.value
        assert orcid_id["nameIdentifierScheme"] == "ORCID"

    def test_datacite_export_person_with_affiliation(self, person, affiliation):
        transform = DataCiteTransform()
        datacite_data = transform.export(person)

        assert "name" in datacite_data
        assert datacite_data["nameType"] == "Personal"

    def test_datacite_import_creates_person(self):
        transform = DataCiteTransform()
        datacite_data = {
            "name": "Doe, Jane",
            "givenName": "Jane",
            "familyName": "Doe",
            "nameType": "Personal",
            "nameIdentifiers": [
                {
                    "nameIdentifier": "0000-0002-1234-5678",
                    "nameIdentifierScheme": "ORCID",
                }
            ],
        }

        person = transform.import_data(datacite_data)

        assert person.first_name == "Jane"
        assert person.last_name == "Doe"
        assert "Doe" in person.name and "Jane" in person.name


@pytest.mark.django_db
class TestSchemaOrgOrganizationExport:
    def test_schema_org_export_organization_basic(self, organization):
        transform = SchemaOrgTransform()
        schema_org_data = transform.export(organization)

        assert schema_org_data["@type"] == "Organization"
        assert schema_org_data["name"] == organization.name

    def test_schema_org_export_organization_with_ror(
        self, organization, ror_identifier
    ):
        transform = SchemaOrgTransform()
        schema_org_data = transform.export(organization)

        assert "@id" in schema_org_data
        assert ror_identifier.value in schema_org_data["@id"]

    def test_schema_org_import_creates_organization(self):
        transform = SchemaOrgTransform()
        schema_org_data = {
            "@type": "Organization",
            "name": "University of Example",
            "identifier": "https://ror.org/02nr0ka47",
        }

        org = transform.import_data(schema_org_data)

        assert org.name == "University of Example"
        assert isinstance(org, Organization)


@pytest.mark.django_db
class TestCSLJSONExport:
    def test_csl_json_export_person(self, person):
        transform = CSLJSONTransform()
        csl_data = transform.export(person)

        assert "family" in csl_data
        assert csl_data["family"] == person.last_name
        assert "given" in csl_data
        assert csl_data["given"] == person.first_name


@pytest.mark.django_db
class TestORCIDRoundTrip:
    def test_orcid_export_person(self, person, orcid_identifier):
        transform = ORCIDTransform()
        orcid_data = transform.export(person)

        assert "person" in orcid_data
        assert "name" in orcid_data["person"]

    def test_orcid_import_person(self):
        transform = ORCIDTransform()
        orcid_api_data = {
            "person": {
                "name": {
                    "given-names": {"value": "John"},
                    "family-name": {"value": "Smith"},
                },
            },
        }

        person = transform.import_data(orcid_api_data)

        assert person.first_name == "John"
        assert person.last_name == "Smith"


@pytest.mark.django_db
class TestRORRoundTrip:
    def test_ror_export_organization(self, organization, ror_identifier):
        transform = RORTransform()
        ror_data = transform.export(organization)

        assert "name" in ror_data
        assert ror_data["name"] == organization.name

    def test_ror_import_organization(self, recorded):
        org = RORTransform().import_data(recorded("ror-record"))

        assert isinstance(org, Organization)
        assert org.name == "GFZ Helmholtz Centre for Geosciences"
        assert org.city == "Potsdam"
        assert org.country.code == "DE"
        assert float(org.location.latitude) == pytest.approx(52.39886)
        assert float(org.location.longitude) == pytest.approx(13.06566)
        assert org.identifiers.get(type="ROR").value == "04z8jg394"

    def test_ror_import_reads_other_names_and_links(self, recorded):
        org = RORTransform().import_data(recorded("ror-record"), save=False)

        assert org.alternative_names == [
            "Helmholtz Centre Potsdam - GFZ German Research Centre for Geosciences",
            "Helmholtz-Zentrum Potsdam - Deutsches GeoForschungsZentrum GFZ",
            "GFZ",
        ]
        assert org.links == [
            "https://www.gfz.de",
            "https://en.wikipedia.org/wiki/GFZ_Helmholtz_Centre_for_Geosciences",
        ]

    def test_ror_import_without_a_location_leaves_it_empty(self, recorded):
        body = recorded("ror-record")
        body["locations"] = []

        org = RORTransform().import_data(body, save=False)

        assert not org.city
        assert not org.country
        assert org.location is None

    def test_ror_fetch_asks_for_the_version_2_record(self, registry_network, recorded):
        address = "https://api.ror.org/v2/organizations/04z8jg394"
        registry_network.answer(address, recorded("ror-record"))

        RORTransform.fetch_from_api("https://ror.org/04z8jg394")

        assert [call.url for call in registry_network.calls] == [address]


@pytest.mark.django_db
class TestTransformValidation:
    def test_datacite_validates_correct_structure(self):
        transform = DataCiteTransform()
        valid_data = {
            "name": "Doe, Jane",
            "nameType": "Personal",
        }

        assert transform.validate(valid_data) is True

    def test_schema_org_validates_correct_structure(self):
        transform = SchemaOrgTransform()
        valid_data = {
            "@type": "Organization",
            "name": "Test Org",
        }

        assert transform.validate(valid_data) is True
