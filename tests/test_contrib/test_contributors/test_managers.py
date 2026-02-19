"""
Tests for Contributor Manager methods (Phase 10, User Story 6).

This module tests custom manager methods for:
- PersonalContributorsManager: claimed(), unclaimed()
- ContributionManager: by_role(), for_entity(), by_contributor()
- Duplicate detection utilities

Tests correspond to tasks T100-T103.
"""

import pytest

from fairdm.contrib.contributors.models import Contribution, Person
from fairdm.contrib.contributors.tasks import detect_duplicate_contributors

# ── T100: claimed/unclaimed querysets ────────────────────────────────────────


class TestPersonQuerysets:
    """Test PersonalContributorsManager queryset methods."""

    @pytest.mark.django_db
    def test_claimed_queryset(self, person):
        """Person.objects.claimed() returns only claimed persons (email + active)."""
        # Create an unclaimed person
        unclaimed = Person.objects.create_unclaimed(
            first_name="Unclaimed",
            last_name="Test",
        )

        claimed_persons = Person.objects.claimed()

        # Claimed person should be in queryset
        assert person in claimed_persons
        # Unclaimed person should NOT be in queryset
        assert unclaimed not in claimed_persons

    @pytest.mark.django_db
    def test_unclaimed_queryset(self, unclaimed_person):
        """Person.objects.unclaimed() returns only unclaimed persons (no email)."""
        # Create a claimed person
        claimed = Person.objects.create(
            email="claimed@example.com",
            first_name="Claimed",
            last_name="Test",
            is_active=True,
            is_claimed=True,  # Mark as claimed
        )
        claimed.set_password("testpass123")
        claimed.save()

        unclaimed_persons = Person.objects.unclaimed()

        # Unclaimed person should be in queryset
        assert unclaimed_person in unclaimed_persons
        # Claimed person should NOT be in queryset
        assert claimed not in unclaimed_persons

    @pytest.mark.django_db
    def test_claimed_excludes_inactive_with_email(self):
        """Claimed queryset excludes inactive persons even if they have email."""
        inactive = Person.objects.create(
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            is_active=False,  # Not active
        )

        claimed_persons = Person.objects.claimed()

        # Inactive person with email should NOT be in claimed queryset
        assert inactive not in claimed_persons


# ── T101: ContributionManager.by_role() ──────────────────────────────────────


class TestContributionByRole:
    """Test ContributionManager.by_role() method."""

    @pytest.mark.django_db
    def test_by_role_filters_correctly(self, contribution):
        """by_role() returns only contributions with specified role."""
        from research_vocabs.models import Concept, Vocabulary

        # Get or create a test role
        vocab, _ = Vocabulary.objects.get_or_create(name="fairdm-roles")
        role, _ = Concept.objects.get_or_create(
            vocabulary=vocab,
            name="TestRole",
        )

        # Add role to the contribution
        contribution.roles.add(role)
        contribution.save()

        # Filter by the role
        qs = Contribution.objects.by_role("TestRole")

        # Should find the contribution
        assert qs.count() > 0
        assert contribution in qs

    @pytest.mark.django_db
    def test_by_role_excludes_non_matching(self, contribution):
        """by_role() excludes contributions without the specified role."""
        # Don't add any roles to contribution
        # Search for a role that doesn't exist on this contribution
        qs = Contribution.objects.by_role("NonExistentRole")

        # Should not find the contribution
        assert contribution not in qs


# ── T102: ContributionManager.for_entity() ───────────────────────────────────


class TestContributionForEntity:
    """Test ContributionManager.for_entity() method."""

    @pytest.mark.django_db
    def test_for_entity_filters_by_object(self, contribution, project_for_contributions, organization):
        """for_entity() returns only contributions for the specified entity."""
        from fairdm.factories import ProjectFactory

        # Create another project using factory with the organization as owner
        other_project = ProjectFactory(owner=organization)

        # Get contributions for the original project
        qs = Contribution.objects.for_entity(project_for_contributions)

        # Should find the contribution linked to project_for_contributions
        assert contribution in qs

        # Should not include contributions for other projects
        other_qs = Contribution.objects.for_entity(other_project)
        assert contribution not in other_qs

    @pytest.mark.django_db
    def test_for_entity_returns_empty_for_new_object(self, organization):
        """for_entity() returns empty queryset for objects with no contributors."""
        from fairdm.factories import ProjectFactory

        # Create a project with no contributors using factory
        new_project = ProjectFactory(owner=organization)

        # Remove default contributor if any
        new_project.contributors.all().delete()

        qs = Contribution.objects.for_entity(new_project)

        # Should be empty
        assert qs.count() == 0


# ── T103: Duplicate detection utility ────────────────────────────────────────


class TestDuplicateDetection:
    """Test duplicate contributor detection utility."""

    @pytest.mark.django_db
    def test_detect_duplicate_contributors(self):
        """detect_duplicate_contributors() finds persons with similar names."""
        # Create persons with same normalized names
        Person.objects.create_unclaimed(
            first_name="John",
            last_name="Smith",
        )
        Person.objects.create_unclaimed(
            first_name="John",
            last_name="Smith",
        )

        # Run duplicate detection
        result = detect_duplicate_contributors()

        # Should find duplicate groups
        assert result["groups_found"] > 0
        assert result["total_duplicates"] >= 2

    @pytest.mark.django_db
    def test_no_duplicates_when_names_differ(self):
        """detect_duplicate_contributors() returns no duplicates for unique names."""
        # Create persons with different names
        Person.objects.create_unclaimed(
            first_name="Alice",
            last_name="Johnson",
        )
        Person.objects.create_unclaimed(
            first_name="Bob",
            last_name="Williams",
        )

        # Run duplicate detection
        result = detect_duplicate_contributors()

        # Should find no duplicates
        assert result["total_duplicates"] == 0


# ── T075a: Affiliation queryset methods ──────────────────────────────────────


class TestAffiliationQuerysetMethods:
    """Test AffiliationQuerySet methods: primary(), current(), past()."""

    @pytest.mark.django_db
    def test_affiliation_primary_method(self, db):
        """primary() returns the affiliation with is_primary=True."""
        from fairdm.factories import AffiliationFactory, OrganizationFactory, PersonFactory

        person = PersonFactory()
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")

        # Create non-primary affiliation
        aff1 = AffiliationFactory(
            person=person,
            organization=org1,
            is_primary=False,
        )

        # Create primary affiliation
        aff2 = AffiliationFactory(
            person=person,
            organization=org2,
            is_primary=True,
        )

        # Test primary() method
        primary = person.affiliations.primary()
        assert primary == aff2
        assert primary.is_primary is True

    @pytest.mark.django_db
    def test_affiliation_primary_returns_none_when_no_primary(self, db):
        """primary() returns None when no affiliation is marked primary."""
        from fairdm.factories import AffiliationFactory, OrganizationFactory, PersonFactory

        person = PersonFactory()
        org = OrganizationFactory()

        # Create non-primary affiliation
        AffiliationFactory(
            person=person,
            organization=org,
            is_primary=False,
        )

        # Test primary() returns None
        primary = person.affiliations.primary()
        assert primary is None

    @pytest.mark.django_db
    def test_affiliation_current_method(self, db):
        """current() returns affiliations with end_date=None."""
        from fairdm.factories import AffiliationFactory, OrganizationFactory, PersonFactory

        person = PersonFactory()
        org1 = OrganizationFactory(name="Current Org")
        org2 = OrganizationFactory(name="Past Org")

        # Create current affiliation (no end date)
        current_aff = AffiliationFactory(
            person=person,
            organization=org1,
            start_date="2020",
            end_date=None,
        )

        # Create past affiliation (with end date)
        past_aff = AffiliationFactory(
            person=person,
            organization=org2,
            start_date="2015",
            end_date="2019",
        )

        # Test current() method
        current_affiliations = person.affiliations.current()
        assert current_affiliations.count() == 1
        assert current_aff in current_affiliations
        assert past_aff not in current_affiliations

    @pytest.mark.django_db
    def test_affiliation_past_method(self, db):
        """past() returns affiliations with end_date IS NOT NULL."""
        from fairdm.factories import AffiliationFactory, OrganizationFactory, PersonFactory

        person = PersonFactory()
        org1 = OrganizationFactory(name="Current Org")
        org2 = OrganizationFactory(name="Past Org")

        # Create current affiliation (no end date)
        current_aff = AffiliationFactory(
            person=person,
            organization=org1,
            start_date="2020",
            end_date=None,
        )

        # Create past affiliation (with end date)
        past_aff = AffiliationFactory(
            person=person,
            organization=org2,
            start_date="2015",
            end_date="2019",
        )

        # Test past() method
        past_affiliations = person.affiliations.past()
        assert past_affiliations.count() == 1
        assert past_aff in past_affiliations
        assert current_aff not in past_affiliations

    @pytest.mark.django_db
    def test_affiliation_current_and_past_mutually_exclusive(self, db):
        """current() and past() return mutually exclusive querysets."""
        from fairdm.factories import AffiliationFactory, OrganizationFactory, PersonFactory

        person = PersonFactory()
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")
        org3 = OrganizationFactory(name="Org 3")

        # Create current affiliations
        AffiliationFactory(
            person=person,
            organization=org1,
            end_date=None,
        )
        AffiliationFactory(
            person=person,
            organization=org2,
            end_date=None,
        )

        # Create past affiliation
        AffiliationFactory(
            person=person,
            organization=org3,
            end_date="2020",
        )

        # Test mutual exclusivity
        current = person.affiliations.current()
        past = person.affiliations.past()

        assert current.count() == 2
        assert past.count() == 1

        # No overlap
        assert set(current) & set(past) == set()
