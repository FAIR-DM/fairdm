"""Tests for contributor transformation utilities (DataCite, Schema.org, etc.)."""

import pytest

from fairdm.contrib.contributors.models import ContributorIdentifier, OrganizationMember
from fairdm.contrib.contributors.utils import (
    contributor_to_datacite,
    contributor_to_schema_org,
)
from fairdm.factories.contributors import OrganizationFactory, PersonFactory


@pytest.mark.django_db
class TestDataCiteExport:
    """Tests for DataCite metadata export (to_datacite method)."""

    def test_person_to_datacite_basic(self):
        """Test basic Person export to DataCite format."""
        person = PersonFactory(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
        )

        result = contributor_to_datacite(person)

        assert result["name"] == person.name
        assert result["nameType"] == "Personal"
        assert result["givenName"] == "Jane"
        assert result["familyName"] == "Doe"

    def test_person_to_datacite_with_orcid(self):
        """Test Person export includes ORCID identifier."""
        person = PersonFactory(first_name="John", last_name="Smith")
        ContributorIdentifier.objects.create(
            related=person,
            type="ORCID",
            value="0000-0002-1825-0097",
        )

        result = contributor_to_datacite(person)

        assert "nameIdentifiers" in result
        assert len(result["nameIdentifiers"]) == 1
        assert result["nameIdentifiers"][0]["nameIdentifier"] == "0000-0002-1825-0097"
        assert result["nameIdentifiers"][0]["nameIdentifierScheme"] == "ORCID"

    def test_person_to_datacite_with_affiliation(self):
        """Test Person export includes primary affiliation."""
        org = OrganizationFactory(name="Test University")
        person = PersonFactory(first_name="Alice", last_name="Jones")

        OrganizationMember.objects.create(
            person=person,
            organization=org,
            is_primary=True,
        )

        result = contributor_to_datacite(person)

        assert "affiliation" in result
        assert len(result["affiliation"]) == 1
        assert result["affiliation"][0]["name"] == "Test University"

    def test_person_to_datacite_with_affiliation_ror(self):
        """Test Person export includes affiliation ROR identifier."""
        org = OrganizationFactory(name="Research Institute")
        ContributorIdentifier.objects.create(
            related=org,
            type="ROR",
            value="05dxps055",
        )

        person = PersonFactory(first_name="Bob", last_name="Wilson")
        OrganizationMember.objects.create(
            person=person,
            organization=org,
            is_primary=True,
        )

        result = contributor_to_datacite(person)

        assert result["affiliation"][0]["affiliationIdentifier"] == "05dxps055"
        assert result["affiliation"][0]["affiliationIdentifierScheme"] == "ROR"

    def test_organization_to_datacite_basic(self):
        """Test basic Organization export to DataCite format."""
        org = OrganizationFactory(name="Example Corp")

        result = contributor_to_datacite(org)

        assert result["name"] == "Example Corp"
        assert result["nameType"] == "Organizational"
        assert "givenName" not in result
        assert "familyName" not in result

    def test_organization_to_datacite_with_ror(self):
        """Test Organization export includes ROR identifier."""
        org = OrganizationFactory(name="University of Example")
        ContributorIdentifier.objects.create(
            related=org,
            type="ROR",
            value="01an7q238",
        )

        result = contributor_to_datacite(org)

        assert "nameIdentifiers" in result
        assert result["nameIdentifiers"][0]["nameIdentifier"] == "01an7q238"
        assert result["nameIdentifiers"][0]["nameIdentifierScheme"] == "ROR"


@pytest.mark.django_db
class TestSchemaOrgExport:
    """Tests for Schema.org JSON-LD export (to_schema_org method)."""

    def test_person_to_schema_org_basic(self):
        """Test basic Person export to Schema.org format."""
        person = PersonFactory(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            profile="Research scientist",
        )

        result = contributor_to_schema_org(person)

        assert result["@type"] == "Person"
        assert result["name"] == person.name
        assert result["givenName"] == "Jane"
        assert result["familyName"] == "Doe"
        assert result["email"] == "jane@example.com"
        assert result["description"] == "Research scientist"

    def test_person_to_schema_org_with_orcid(self):
        """Test Person export includes ORCID as @id."""
        person = PersonFactory(first_name="John", last_name="Smith")
        ContributorIdentifier.objects.create(
            related=person,
            type="ORCID",
            value="0000-0002-1825-0097",
        )

        result = contributor_to_schema_org(person)

        assert result["@id"] == "https://orcid.org/0000-0002-1825-0097"

    def test_person_to_schema_org_with_affiliation(self):
        """Test Person export includes affiliation as nested Organization."""
        org = OrganizationFactory(name="Test University")
        person = PersonFactory(first_name="Alice", last_name="Jones")

        OrganizationMember.objects.create(
            person=person,
            organization=org,
            is_primary=True,
        )

        result = contributor_to_schema_org(person)

        assert "affiliation" in result
        assert result["affiliation"]["@type"] == "Organization"
        assert result["affiliation"]["name"] == "Test University"

    def test_person_to_schema_org_with_affiliation_ror(self):
        """Test Person export includes affiliation ROR as @id."""
        org = OrganizationFactory(name="Research Institute")
        ContributorIdentifier.objects.create(
            related=org,
            type="ROR",
            value="05dxps055",
        )

        person = PersonFactory(first_name="Bob", last_name="Wilson")
        OrganizationMember.objects.create(
            person=person,
            organization=org,
            is_primary=True,
        )

        result = contributor_to_schema_org(person)

        assert result["affiliation"]["@id"] == "https://ror.org/05dxps055"

    def test_person_to_schema_org_with_links(self):
        """Test Person export includes URL from links field."""
        person = PersonFactory(
            first_name="Charlie",
            last_name="Brown",
            links=["https://example.com/charlie", "https://github.com/charlie"],
        )

        result = contributor_to_schema_org(person)

        assert result["url"] == "https://example.com/charlie"  # First link

    def test_organization_to_schema_org_basic(self):
        """Test basic Organization export to Schema.org format."""
        org = OrganizationFactory(
            name="Example Corp",
            profile="Leading research organization",
        )

        result = contributor_to_schema_org(org)

        assert result["@type"] == "Organization"
        assert result["name"] == "Example Corp"
        assert result["description"] == "Leading research organization"

    def test_organization_to_schema_org_with_ror(self):
        """Test Organization export includes ROR as @id."""
        org = OrganizationFactory(name="University of Example")
        ContributorIdentifier.objects.create(
            related=org,
            type="ROR",
            value="01an7q238",
        )

        result = contributor_to_schema_org(org)

        assert result["@id"] == "https://ror.org/01an7q238"

    def test_organization_to_schema_org_with_location(self):
        """Test Organization export includes address from city/country."""
        org = OrganizationFactory(
            name="Paris Research Center",
            city="Paris",
            country="FR",
        )

        result = contributor_to_schema_org(org)

        assert "address" in result
        assert result["address"]["@type"] == "PostalAddress"
        assert result["address"]["addressLocality"] == "Paris"
        assert result["address"]["addressCountry"] == "FR"

    def test_organization_to_schema_org_with_links(self):
        """Test Organization export includes URL from links field."""
        org = OrganizationFactory(
            name="Tech Company",
            links=["https://techcompany.com"],
        )

        result = contributor_to_schema_org(org)

        assert result["url"] == "https://techcompany.com"


@pytest.mark.django_db
class TestModelMethods:
    """Test the to_datacite() and to_schema_org() methods on models."""

    def test_person_model_to_datacite_method(self):
        """Test Person.to_datacite() method works."""
        person = PersonFactory(first_name="Test", last_name="User")
        result = person.to_datacite()

        assert result["name"] == person.name
        assert result["nameType"] == "Personal"

    def test_person_model_to_schema_org_method(self):
        """Test Person.to_schema_org() method works."""
        person = PersonFactory(first_name="Test", last_name="User")
        result = person.to_schema_org()

        assert result["@type"] == "Person"
        assert result["name"] == person.name

    def test_organization_model_to_datacite_method(self):
        """Test Organization.to_datacite() method works."""
        org = OrganizationFactory(name="Test Org")
        result = org.to_datacite()

        assert result["name"] == "Test Org"
        assert result["nameType"] == "Organizational"

    def test_organization_model_to_schema_org_method(self):
        """Test Organization.to_schema_org() method works."""
        org = OrganizationFactory(name="Test Org")
        result = org.to_schema_org()

        assert result["@type"] == "Organization"
        assert result["name"] == "Test Org"
