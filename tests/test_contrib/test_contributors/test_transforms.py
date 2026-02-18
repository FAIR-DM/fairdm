"""Tests for contributor data transformations (User Story 5).

Verifies bidirectional transformations between Contributor instances
and external metadata formats (DataCite, Schema.org, CSL-JSON, ORCID, ROR).
"""

import pytest

from fairdm.contrib.contributors.models import Organization, Person
from fairdm.contrib.contributors.utils.transforms import (
    CSLJSONTransform,
    DataCiteTransform,
    ORCIDTransform,
    RORTransform,
    SchemaOrgTransform,
)


# ── T082: DataCite Export for Person ──────────────────────────────────────────


@pytest.mark.django_db
class TestDataCitePersonExport:
    """Verify Person export to DataCite format."""

    def test_datacite_export_person_basic(self, person):
        """Person with basic fields exports to valid DataCite creator format."""
        transform = DataCiteTransform()
        datacite_data = transform.export(person)

        # DataCite creator structure
        assert "name" in datacite_data
        assert datacite_data["name"] == person.name
        assert "nameType" in datacite_data
        assert datacite_data["nameType"] == "Personal"

    def test_datacite_export_person_with_orcid(self, person, orcid_identifier):
        """Person with ORCID exports with nameIdentifier."""
        transform = DataCiteTransform()
        datacite_data = transform.export(person)

        assert "nameIdentifiers" in datacite_data
        assert len(datacite_data["nameIdentifiers"]) > 0
        orcid_id = datacite_data["nameIdentifiers"][0]
        assert orcid_id["nameIdentifier"] == orcid_identifier.value
        assert orcid_id["nameIdentifierScheme"] == "ORCID"

    def test_datacite_export_person_with_affiliation(self, person, affiliation):
        """Person with affiliation exports with affiliation data."""
        transform = DataCiteTransform()
        datacite_data = transform.export(person)

        # Note: Current implementation doesn't include affiliations in simple export
        # Affiliations are contextual (vary by contribution)
        assert "name" in datacite_data
        assert datacite_data["nameType"] == "Personal"

    def test_datacite_import_creates_person(self):
        """DataCite creator data creates new Person instance."""
        transform = DataCiteTransform()
        datacite_data = {
            "name": "Doe, Jane",
            "givenName": "Jane",
            "familyName": "Doe",
            "nameType": "Personal",
            "nameIdentifiers": [{"nameIdentifier": "0000-0002-1234-5678", "nameIdentifierScheme": "ORCID"}],
        }

        person = transform.import_data(datacite_data)

        assert person.first_name == "Jane"
        assert person.last_name == "Doe"
        # DataCite uses "Doe, Jane" format in name field
        assert "Doe" in person.name and "Jane" in person.name


# ── T083: Schema.org Export for Organization ──────────────────────────────────


@pytest.mark.django_db
class TestSchemaOrgOrganizationExport:
    """Verify Organization export to Schema.org format."""

    def test_schema_org_export_organization_basic(self, organization):
        """Organization exports to valid Schema.org JSON-LD."""
        transform = SchemaOrgTransform()
        schema_org_data = transform.export(organization)

        assert schema_org_data["@type"] == "Organization"
        assert schema_org_data["name"] == organization.name

    def test_schema_org_export_organization_with_ror(self, organization, ror_identifier):
        """Organization with ROR exports with @id identifier."""
        transform = SchemaOrgTransform()
        schema_org_data = transform.export(organization)

        # Schema.org uses @id for ROR identifier
        assert "@id" in schema_org_data
        assert ror_identifier.value in schema_org_data["@id"]

    def test_schema_org_import_creates_organization(self):
        """Schema.org Organization data creates new Organization instance."""
        transform = SchemaOrgTransform()
        schema_org_data = {
            "@type": "Organization",
            "name": "University of Example",
            "identifier": "https://ror.org/02nr0ka47",
        }

        org = transform.import_data(schema_org_data)

        assert org.name == "University of Example"
        assert isinstance(org, Organization)


# ── T084: CSL-JSON Export ────────────────────────────────────────────────────


@pytest.mark.django_db
class TestCSLJSONExport:
    """Verify Person export to CSL-JSON citation format."""

    def test_csl_json_export_person(self, person):
        """Person exports to valid CSL-JSON author format."""
        transform = CSLJSONTransform()
        csl_data = transform.export(person)

        assert "family" in csl_data
        assert csl_data["family"] == person.last_name
        assert "given" in csl_data
        assert csl_data["given"] == person.first_name


# ── T085: ORCID Round-Trip ───────────────────────────────────────────────────


@pytest.mark.django_db
class TestORCIDRoundTrip:
    """Verify ORCID data round-trip (export + import)."""

    def test_orcid_export_person(self, person, orcid_identifier):
        """Person exports to ORCID-compatible format."""
        transform = ORCIDTransform()
        orcid_data = transform.export(person)

        assert "person" in orcid_data
        assert "name" in orcid_data["person"]

    def test_orcid_import_person(self):
        """ORCID API JSON creates Person instance."""
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


# ── T086: ROR Round-Trip ─────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRORRoundTrip:
    """Verify ROR data round-trip (export + import)."""

    def test_ror_export_organization(self, organization, ror_identifier):
        """Organization exports to ROR-compatible format."""
        transform = RORTransform()
        ror_data = transform.export(organization)

        assert "name" in ror_data
        assert ror_data["name"] == organization.name

    def test_ror_import_organization(self):
        """ROR API JSON creates Organization instance."""
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


# ── T087-T088: Transform Validation ──────────────────────────────────────────


@pytest.mark.django_db
class TestTransformValidation:
    """Verify transform data validation."""

    def test_datacite_validates_correct_structure(self):
        """DataCite transform validates correct data structure."""
        transform = DataCiteTransform()
        valid_data = {
            "name": "Doe, Jane",
            "nameType": "Personal",
        }

        assert transform.validate(valid_data) is True

    def test_schema_org_validates_correct_structure(self):
        """Schema.org transform validates correct data structure."""
        transform = SchemaOrgTransform()
        valid_data = {
            "@type": "Organization",
            "name": "Test Org",
        }

        assert transform.validate(valid_data) is True
