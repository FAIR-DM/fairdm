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

    def test_ror_import_organization(self):
        transform = RORTransform()
        ror_api_data = {
            "name": "Test University",
            "id": "https://ror.org/02nr0ka47",
            "addresses": [
                {
                    "city": "Boston",
                    "lat": 42.3601,
                    "lng": -71.0589,
                }
            ],
            "country": {"country_code": "US"},
        }

        org = transform.import_data(ror_api_data)

        assert org.name == "Test University"
        assert isinstance(org, Organization)
        assert org.city == "Boston"


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
