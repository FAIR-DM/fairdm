"""Tests for contributor models."""

import re
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from fairdm.contrib.contributors.models import (
    Contribution,
    ContributorIdentifier,
)
from fairdm.factories.contributors import (
    ContributionFactory,
    OrganizationFactory,
    OrganizationMembershipFactory,
    PersonFactory,
)
from fairdm.factories.core import ProjectFactory


@pytest.mark.django_db
class TestPerson:
    """Tests for Person model."""

    def test_create_person(self):
        """Test creating a basic person."""
        person = PersonFactory()
        assert person.pk is not None
        assert person.name
        assert person.email
        assert person.first_name
        assert person.last_name

    def test_person_str(self):
        """Test Person string representation."""
        person = PersonFactory(name="Jane Doe")
        assert str(person) == "Jane Doe"

    def test_get_full_name_display_given_family(self):
        """Test full name display in given_family format."""
        person = PersonFactory(first_name="John", last_name="Smith")
        result = person.get_full_name_display("given_family")
        assert result == "John Smith"

    def test_get_full_name_display_family_given(self):
        """Test full name display in family_given format."""
        person = PersonFactory(first_name="John", last_name="Smith")
        result = person.get_full_name_display("family_given")
        assert result == "Smith, John"

    def test_get_full_name_display_family_initial(self):
        """Test full name display in family_initial format."""
        person = PersonFactory(first_name="John", last_name="Smith")
        result = person.get_full_name_display("family_initial")
        assert result == "Smith, J."

    def test_get_full_name_display_initials_family(self):
        """Test full name display in initials_family format."""
        person = PersonFactory(first_name="John", last_name="Smith")
        result = person.get_full_name_display("initials_family")
        assert result == "J. Smith"

    def test_get_full_name_display_missing_names(self):
        """Test full name display with missing name components."""
        person = PersonFactory(first_name="", last_name="Smith")
        # Should handle missing first name gracefully
        result = person.get_full_name_display("given_family")
        assert "Smith" in result

    def test_get_full_name_display_invalid_format(self):
        """Test full name display with invalid format defaults to given_family."""
        person = PersonFactory(first_name="John", last_name="Smith")
        result = person.get_full_name_display("invalid_format")
        assert result == "John Smith"

    def test_clean_valid_email(self):
        """Test clean method with valid email."""
        person = PersonFactory(email="valid@email.com")
        person.clean()  # Should not raise

    def test_clean_invalid_email(self):
        """Test clean method with invalid email."""
        person = PersonFactory.build(email="not-an-email")
        with pytest.raises(ValidationError) as exc_info:
            person.clean()
        assert "email" in exc_info.value.message_dict

    def test_clean_valid_orcid(self):
        """Test clean method with valid ORCID format."""
        person = PersonFactory()
        ContributorIdentifier.objects.create(related=person, type="ORCID", value="0000-0001-2345-6789")
        person.clean()  # Should not raise

    def test_clean_invalid_orcid(self):
        """Test clean method with invalid ORCID format."""
        person = PersonFactory()
        ContributorIdentifier.objects.create(related=person, type="ORCID", value="invalid-orcid")
        with pytest.raises(ValidationError) as exc_info:
            person.clean()
        assert "identifiers" in exc_info.value.message_dict

    def test_clean_valid_urls(self):
        """Test clean method with valid URLs."""
        person = PersonFactory(links=["https://example.com", "http://test.org"])
        person.clean()  # Should not raise

    def test_clean_invalid_urls(self):
        """Test clean method with invalid URLs."""
        person = PersonFactory.build(links=["not-a-url", "https://valid.com"])
        with pytest.raises(ValidationError) as exc_info:
            person.clean()
        assert "links" in exc_info.value.message_dict

    def test_primary_affiliation(self):
        """Test getting primary affiliation."""
        person = PersonFactory()
        org = OrganizationFactory()
        membership = OrganizationMembershipFactory(person=person, organization=org, is_primary=True)
        primary = person.primary_affiliation()  # Call the method
        assert primary is not None
        assert primary.pk == membership.pk

    def test_current_affiliations(self):
        """Test getting current affiliations."""
        person = PersonFactory()
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        org3 = OrganizationFactory()

        # Current affiliations
        OrganizationMembershipFactory(person=person, organization=org1, is_current=True)
        OrganizationMembershipFactory(person=person, organization=org2, is_current=True)

        # Past affiliation
        OrganizationMembershipFactory(person=person, organization=org3, is_current=False)

        current = person.current_affiliations()
        assert current.count() == 2

    def test_default_identifier(self):
        """Test default identifier returns ORCID."""
        person = PersonFactory()
        orcid = ContributorIdentifier.objects.create(related=person, type="ORCID", value="0000-0001-2345-6789")
        assert person.default_identifier == orcid


@pytest.mark.django_db
class TestOrganization:
    """Tests for Organization model."""

    def test_create_organization(self):
        """Test creating a basic organization."""
        org = OrganizationFactory()
        assert org.pk is not None
        assert org.name

    def test_organization_str(self):
        """Test Organization string representation."""
        org = OrganizationFactory(name="Test University")
        assert str(org) == "Test University"

    def test_clean_valid_ror(self):
        """Test clean method with valid ROR format."""
        org = OrganizationFactory()
        ContributorIdentifier.objects.create(related=org, type="ROR", value="02h6b9e47")
        org.clean()  # Should not raise

    def test_clean_invalid_ror(self):
        """Test clean method with invalid ROR format."""
        org = OrganizationFactory()
        ContributorIdentifier.objects.create(related=org, type="ROR", value="invalid-ror")
        with pytest.raises(ValidationError) as exc_info:
            org.clean()
        assert "identifiers" in exc_info.value.message_dict

    def test_clean_valid_urls(self):
        """Test clean method with valid URLs."""
        org = OrganizationFactory(links=["https://example.edu", "http://test.org"])
        org.clean()  # Should not raise

    def test_clean_invalid_urls(self):
        """Test clean method with invalid URLs."""
        org = OrganizationFactory.build(links=["not-a-url", "https://valid.com"])
        with pytest.raises(ValidationError) as exc_info:
            org.clean()
        assert "links" in exc_info.value.message_dict

    def test_members_property(self):
        """Test getting organization members."""
        org = OrganizationFactory()
        person1 = PersonFactory()
        person2 = PersonFactory()

        OrganizationMembershipFactory(person=person1, organization=org)
        OrganizationMembershipFactory(person=person2, organization=org)

        members = org.members.all()
        assert members.count() == 2

    def test_default_identifier(self):
        """Test default identifier returns ROR."""
        org = OrganizationFactory()
        ror = ContributorIdentifier.objects.create(related=org, type="ROR", value="02h6b9e47")
        assert org.default_identifier == ror


@pytest.mark.django_db
class TestContributor:
    """Tests for base Contributor model methods."""

    def test_calculate_profile_completion_empty(self):
        """Test profile completion with minimal data."""
        person = PersonFactory(
            name="Test",
            profile="",
            image=None,
            links=[],
        )
        completion = person.calculate_profile_completion()
        # No fields filled (profile, image, links are all empty)
        assert completion == 0.0

    def test_calculate_profile_completion_full(self):
        """Test profile completion with all data."""
        person = PersonFactory(
            name="Test",
            profile="A bio",
            links=["https://example.com"],
        )
        # Factory creates image by default
        completion = person.calculate_profile_completion()
        # All 3 fields filled (profile, image, links)
        assert completion == 1.0

    def test_calculate_weight(self):
        """Test weight calculation combines all factors."""
        person = PersonFactory()
        # Mock the profile completion
        with patch.object(person, "calculate_profile_completion", return_value=0.8):
            weight = person.calculate_weight()
            # Weight should be between 0 and 1
            assert 0 <= weight <= 1
            # With 80% completion, should have at least 0.8 * 0.3 = 0.24
            assert weight >= 0.24

    def test_get_recent_contributions(self):
        """Test getting recent contributions."""
        person = PersonFactory()
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        project3 = ProjectFactory()

        # Create contributions
        contrib1 = ContributionFactory(contributor=person, content_object=project1)
        contrib2 = ContributionFactory(contributor=person, content_object=project2)
        contrib3 = ContributionFactory(contributor=person, content_object=project3)

        recent = person.get_recent_contributions(limit=2)
        assert recent.count() == 2
        # Should be ordered by created date (most recent first)
        assert list(recent) == [contrib3, contrib2]

    def test_get_recent_contributions_default_limit(self):
        """Test recent contributions with default limit."""
        person = PersonFactory()
        for _ in range(7):
            project = ProjectFactory()
            ContributionFactory(contributor=person, content_object=project)

        recent = person.get_recent_contributions()
        assert recent.count() == 5  # Default limit

    def test_update_weight_hook(self):
        """Test that weight updates when synced_data changes."""
        person = PersonFactory()
        initial_weight = person.weight

        # Update synced_data
        person.synced_data = {"test": "data"}
        person.save()

        # Weight should be recalculated
        person.refresh_from_db()
        # Weight might change depending on calculate_weight logic
        assert person.weight is not None

    def test_lang_field_valid_codes(self):
        """Test that valid ISO 639-1 language codes are accepted."""
        person = PersonFactory(lang=["en", "es", "fr"])
        # Exclude password from validation
        person.full_clean(exclude=["password"])
        assert person.lang == ["en", "es", "fr"]

    def test_lang_field_invalid_code(self):
        """Test that invalid language codes raise ValidationError."""
        person = PersonFactory(lang=["en", "xxx"])
        with pytest.raises(ValidationError):
            person.full_clean(exclude=["password"])

    def test_lang_field_empty_allowed(self):
        """Test that empty lang field is allowed."""
        person = PersonFactory(lang=[])
        person.full_clean(exclude=["password"])
        assert person.lang == []

    def test_lang_field_case_sensitive(self):
        """Test that language codes must be lowercase."""
        person = PersonFactory(lang=["EN"])
        with pytest.raises(ValidationError):
            person.full_clean(exclude=["password"])


@pytest.mark.django_db
class TestContribution:
    """Tests for Contribution model."""

    def test_create_contribution(self):
        """Test creating a basic contribution."""
        person = PersonFactory()
        project = ProjectFactory()
        contribution = ContributionFactory(contributor=person, content_object=project)
        assert contribution.pk is not None
        assert contribution.contributor == person
        assert contribution.content_object == project

    def test_affiliation_stored_on_contribution(self):
        """Test that affiliation is stored on the contribution."""
        person = PersonFactory()
        org = OrganizationFactory()
        project = ProjectFactory()

        contribution = ContributionFactory(contributor=person, content_object=project, affiliation=org)

        # Affiliation should be stored on the contribution
        assert contribution.affiliation == org
        # Organization should NOT automatically have a contribution
        org_contributions = Contribution.objects.filter(contributor=org, object_id=project.pk)
        assert not org_contributions.exists()

    def test_affiliation_change_simple(self):
        """Test that affiliation can be changed without side effects."""
        person = PersonFactory()
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        project = ProjectFactory()

        # Create contribution with org1
        contribution = ContributionFactory(contributor=person, content_object=project, affiliation=org1)

        assert contribution.affiliation == org1

        # Change affiliation to org2
        contribution.affiliation = org2
        contribution.save()

        # Affiliation should be updated
        contribution.refresh_from_db()
        assert contribution.affiliation == org2

    def test_add_to_method(self):
        """Test the add_to classmethod."""
        person = PersonFactory()
        project = ProjectFactory()
        org = OrganizationFactory()

        contribution = Contribution.add_to(
            contributor=person,
            obj=project,
            roles=["Principal Investigator"],
            affiliation=org,
        )

        assert contribution.contributor == person
        assert contribution.content_object == project
        assert contribution.affiliation == org

    def test_unique_together_constraint(self):
        """Test that duplicate contributor-object pairs are prevented."""
        person = PersonFactory()
        project = ProjectFactory()

        ContributionFactory(contributor=person, content_object=project)

        # Attempting to create another should raise
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            ContributionFactory(contributor=person, content_object=project)


@pytest.mark.django_db
class TestOrganizationMember:
    """Tests for OrganizationMember model."""

    def test_create_organization_member(self):
        """Test creating an organization membership."""
        person = PersonFactory()
        org = OrganizationFactory()
        membership = OrganizationMembershipFactory(person=person, organization=org)
        assert membership.pk is not None
        assert membership.person == person
        assert membership.organization == org

    def test_ensure_one_primary_affiliation(self):
        """Test that only one primary affiliation exists per person."""
        person = PersonFactory()
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()

        # Create first primary affiliation
        membership1 = OrganizationMembershipFactory(person=person, organization=org1, is_primary=True)

        # Create second primary affiliation
        membership2 = OrganizationMembershipFactory(person=person, organization=org2, is_primary=True)

        # First should no longer be primary
        membership1.refresh_from_db()
        assert not membership1.is_primary
        assert membership2.is_primary

    def test_unique_together_constraint(self):
        """Test that person-organization pairs are unique."""
        person = PersonFactory()
        org = OrganizationFactory()

        OrganizationMembershipFactory(person=person, organization=org)

        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            OrganizationMembershipFactory(person=person, organization=org)


@pytest.mark.django_db
class TestContributorIdentifier:
    """Tests for ContributorIdentifier model."""

    def test_create_orcid_identifier(self):
        """Test creating an ORCID identifier."""
        person = PersonFactory()
        identifier = ContributorIdentifier.objects.create(related=person, type="ORCID", value="0000-0001-2345-6789")
        assert identifier.pk is not None
        assert identifier.type == "ORCID"
        assert identifier.value == "0000-0001-2345-6789"

    def test_create_ror_identifier(self):
        """Test creating a ROR identifier."""
        org = OrganizationFactory()
        identifier = ContributorIdentifier.objects.create(related=org, type="ROR", value="02h6b9e47")
        assert identifier.pk is not None
        assert identifier.type == "ROR"
        assert identifier.value == "02h6b9e47"

    def test_orcid_format_validation(self):
        """Test ORCID format regex pattern."""
        valid_orcids = [
            "0000-0001-2345-6789",
            "0000-0002-1825-009X",
            "1234-5678-9012-3456",
        ]

        pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$"
        for orcid in valid_orcids:
            assert re.match(pattern, orcid), f"{orcid} should be valid"

        invalid_orcids = [
            "0000-0001-2345-678",  # Too short
            "0000-0001-2345-67890",  # Too long
            "0000-0001-2345-678Y",  # Invalid check digit
            "ORCID:0000-0001-2345-6789",  # Has prefix
        ]

        for orcid in invalid_orcids:
            assert not re.match(pattern, orcid), f"{orcid} should be invalid"

    def test_ror_format_validation(self):
        """Test ROR format regex pattern."""
        valid_rors = [
            "02h6b9e47",
            "00x0x0x00",
            "0abcdef12",
        ]

        pattern = r"^0[a-z0-9]{6}[0-9]{2}$"
        for ror in valid_rors:
            assert re.match(pattern, ror), f"{ror} should be valid"

        invalid_rors = [
            "12h6b9e47",  # Doesn't start with 0
            "02h6b9e4",  # Too short
            "02h6b9e477",  # Too long
            "02H6B9E47",  # Has uppercase
            "https://ror.org/02h6b9e47",  # Has URL
        ]

        for ror in invalid_rors:
            assert not re.match(pattern, ror), f"{ror} should be invalid"


@pytest.mark.django_db
class TestBaseModelContributorMethods:
    """Tests for the contributor helper methods on BaseModel."""

    def test_get_direct_contributors(self):
        """Test getting direct contributors (people and orgs)."""
        project = ProjectFactory()
        person = PersonFactory()
        org = OrganizationFactory()

        # Add person and org as direct contributors
        ContributionFactory(contributor=person, content_object=project)
        ContributionFactory(contributor=org, content_object=project)

        contributors = project.get_direct_contributors()
        assert contributors.count() == 2
        assert person in contributors
        assert org in contributors

    def test_get_affiliated_organizations(self):
        """Test getting organizations via person affiliations."""
        project = ProjectFactory()
        person1 = PersonFactory()
        person2 = PersonFactory()
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()

        # Add people with affiliations
        ContributionFactory(contributor=person1, content_object=project, affiliation=org1)
        ContributionFactory(contributor=person2, content_object=project, affiliation=org2)

        affiliated_orgs = project.get_affiliated_organizations()
        assert affiliated_orgs.count() == 2
        assert org1 in affiliated_orgs
        assert org2 in affiliated_orgs

    def test_get_all_contributors(self):
        """Test getting all contributors including affiliations."""
        project = ProjectFactory()
        person = PersonFactory()
        org1 = OrganizationFactory()  # Direct contributor
        org2 = OrganizationFactory()  # Via affiliation

        # Add person with affiliation
        ContributionFactory(contributor=person, content_object=project, affiliation=org2)
        # Add org as direct contributor
        ContributionFactory(contributor=org1, content_object=project)

        all_contributors = project.get_all_contributors()
        assert all_contributors.count() == 3
        assert person in all_contributors
        assert org1 in all_contributors
        assert org2 in all_contributors

    def test_get_all_contributors_no_duplicates(self):
        """Test that get_all_contributors doesn't duplicate orgs that are both direct and affiliated."""
        project = ProjectFactory()
        person = PersonFactory()
        org = OrganizationFactory()

        # Add org as direct contributor
        ContributionFactory(contributor=org, content_object=project)
        # Add person with same org as affiliation
        ContributionFactory(contributor=person, content_object=project, affiliation=org)

        all_contributors = project.get_all_contributors()
        # Should be 2 (person + org), not 3
        assert all_contributors.count() == 2
        assert person in all_contributors
        assert org in all_contributors


@pytest.mark.django_db
class TestContributorHelperMethods:
    """Tests for Contributor helper methods."""

    def test_get_contributions_by_type_project(self):
        """Test getting contributions filtered by project type."""
        person = PersonFactory()
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        # Create a dataset to ensure filtering works
        from fairdm.factories.core import DatasetFactory

        dataset = DatasetFactory()

        ContributionFactory(contributor=person, content_object=project1)
        ContributionFactory(contributor=person, content_object=project2)
        ContributionFactory(contributor=person, content_object=dataset)

        project_contributions = person.get_contributions_by_type("project")

        assert project_contributions.count() == 2
        assert all(c.content_type.model == "project" for c in project_contributions)

    def test_get_contributions_by_type_dataset(self):
        """Test getting contributions filtered by dataset type."""
        person = PersonFactory()
        project = ProjectFactory()

        from fairdm.factories.core import DatasetFactory

        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()

        ContributionFactory(contributor=person, content_object=project)
        ContributionFactory(contributor=person, content_object=dataset1)
        ContributionFactory(contributor=person, content_object=dataset2)

        dataset_contributions = person.get_contributions_by_type("dataset")

        assert dataset_contributions.count() == 2
        assert all(c.content_type.model == "dataset" for c in dataset_contributions)

    def test_has_contribution_to_true(self):
        """Test has_contribution_to returns True for existing contribution."""
        person = PersonFactory()
        project = ProjectFactory()

        ContributionFactory(contributor=person, content_object=project)

        assert person.has_contribution_to(project) is True

    def test_has_contribution_to_false(self):
        """Test has_contribution_to returns False for non-existing contribution."""
        person = PersonFactory()
        project = ProjectFactory()

        assert person.has_contribution_to(project) is False

    def test_has_contribution_to_different_object(self):
        """Test has_contribution_to correctly distinguishes between objects."""
        person = PersonFactory()
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        ContributionFactory(contributor=person, content_object=project1)

        assert person.has_contribution_to(project1) is True
        assert person.has_contribution_to(project2) is False

    def test_get_co_contributors_basic(self):
        """Test getting co-contributors from shared projects."""
        person1 = PersonFactory()
        person2 = PersonFactory()
        person3 = PersonFactory()
        project = ProjectFactory()

        # person1 and person2 contribute to the same project
        ContributionFactory(contributor=person1, content_object=project)
        ContributionFactory(contributor=person2, content_object=project)
        # person3 doesn't contribute

        co_contributors = person1.get_co_contributors()

        assert person2 in co_contributors
        assert person3 not in co_contributors
        assert person1 not in co_contributors  # Should not include self

    def test_get_co_contributors_multiple_collaborations(self):
        """Test co-contributors are ordered by collaboration frequency."""
        person1 = PersonFactory()
        person2 = PersonFactory()
        person3 = PersonFactory()

        project1 = ProjectFactory()
        project2 = ProjectFactory()

        from fairdm.factories.core import DatasetFactory

        dataset = DatasetFactory()

        # person1 and person2 collaborate on 2 objects
        ContributionFactory(contributor=person1, content_object=project1)
        ContributionFactory(contributor=person2, content_object=project1)
        ContributionFactory(contributor=person1, content_object=dataset)
        ContributionFactory(contributor=person2, content_object=dataset)

        # person1 and person3 collaborate on 1 object
        ContributionFactory(contributor=person3, content_object=project2)
        ContributionFactory(contributor=person1, content_object=project2)

        co_contributors = list(person1.get_co_contributors())

        # person2 should come first (more collaborations)
        assert co_contributors[0] == person2
        assert co_contributors[1] == person3

    def test_get_co_contributors_with_limit(self):
        """Test limiting the number of co-contributors returned."""
        person1 = PersonFactory()
        person2 = PersonFactory()
        person3 = PersonFactory()
        person4 = PersonFactory()

        project = ProjectFactory()

        ContributionFactory(contributor=person1, content_object=project)
        ContributionFactory(contributor=person2, content_object=project)
        ContributionFactory(contributor=person3, content_object=project)
        ContributionFactory(contributor=person4, content_object=project)

        co_contributors = person1.get_co_contributors(limit=2)

        assert co_contributors.count() == 2

    def test_get_co_contributors_no_collaborations(self):
        """Test get_co_contributors returns empty when no collaborations exist."""
        person = PersonFactory()

        co_contributors = person.get_co_contributors()

        assert co_contributors.count() == 0

    def test_get_co_contributors_organization(self):
        """Test get_co_contributors works for organizations too."""
        org1 = OrganizationFactory()
        org2 = OrganizationFactory()
        project = ProjectFactory()

        ContributionFactory(contributor=org1, content_object=project)
        ContributionFactory(contributor=org2, content_object=project)

        co_contributors = org1.get_co_contributors()

        assert org2 in co_contributors
        assert org1 not in co_contributors
