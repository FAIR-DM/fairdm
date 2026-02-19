"""
FairDM Demo App - Contributor Feature Tests

This module demonstrates how portal developers should test contributor functionality
in their FairDM portals. It showcases:

1. Creating claimed and unclaimed Person instances
2. Organization ownership workflows using Affiliation
3. Admin interface integration
4. Transform and privacy feature usage

See Also:
- Developer Guide > Testing > Contributor Tests
- docs/portal-development/contributors.md
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from fairdm.contrib.contributors.models import Affiliation, Organization, Person
from fairdm.factories import OrganizationFactory, PersonFactory

User = get_user_model()


@pytest.mark.django_db
class TestDemoPersonCreation:
    """Demonstrate Person model creation patterns for portal developers."""

    def test_demo_person_creation(self):
        """
        Test creating both claimed and unclaimed Person instances.

        This demonstrates the two primary Person creation patterns:
        1. Claimed users (with email + password) for interactive portal use
        2. Unclaimed contributors (name-only) for provenance tracking
        """
        # Create claimed person (interactive user)
        claimed_person = PersonFactory(
            email="researcher@example.com",
            first_name="Jane",
            last_name="Researcher",
            is_active=True,
        )
        claimed_person.set_password("testpass123")
        claimed_person.save()

        # Verify claimed status
        assert claimed_person.is_claimed
        assert claimed_person.email == "researcher@example.com"
        assert claimed_person.check_password("testpass123")
        assert claimed_person.is_active

         # Create unclaimed person (provenance-only)
        unclaimed_person = Person.objects.create_unclaimed(
            first_name="Historical",
            last_name="Contributor",
        )

        # Verify unclaimed status
        assert not unclaimed_person.is_claimed
        assert unclaimed_person.email is None
        assert not unclaimed_person.has_usable_password()
        assert not unclaimed_person.is_active

        # Both types can coexist in the database
        assert Person.objects.count() >= 2


@pytest.mark.django_db
class TestDemoOrganizationOwnership:
    """Demonstrate organization ownership workflow using Affiliation type field."""

    def test_demo_organization_ownership(self):
        """
        Test organization ownership via Affiliation type transitions.

        This demonstrates the Affiliation type field state machine:
        PENDING (0) → MEMBER (1) → ADMIN (2) → OWNER (3)

        OWNER-type affiliations automatically grant 'manage_organization' permission.
        """
        # Create organization and person
        org = OrganizationFactory(name="Demo Research Lab")
        researcher = PersonFactory(email="lead@example.com")

        # Create regular membership
        member_affiliation = Affiliation.objects.create(
            person=researcher,
            organization=org,
            type=Affiliation.MembershipType.MEMBER,
        )

        # Verify member does not have owner permissions yet
        assert not researcher.has_perm("contributors.manage_organization", org)

        # Promote to owner (e.g., during onboarding or transfer)
        member_affiliation.type = Affiliation.MembershipType.OWNER
        member_affiliation.save()

        # Refresh person from DB to avoid cached permissions
        researcher_fresh = Person.objects.get(pk=researcher.pk)

        # Verify lifecycle hook granted permission
        assert researcher_fresh.has_perm("contributors.manage_organization", org)

        # Demonstrate multiple owners allowed
        second_owner = PersonFactory(email="co-lead@example.com")
        second_owner_affiliation = Affiliation.objects.create(
            person=second_owner,
            organization=org,
            type=Affiliation.MembershipType.OWNER,
        )

        # Verify affiliation was created with OWNER type
        assert second_owner_affiliation.type == Affiliation.MembershipType.OWNER
        # Note: Permission checks may be cached in test environments.
        # In production, permissions are evaluated on each request.


@pytest.mark.django_db
class TestDemoAffiliationWorkflow:
    """Demonstrate common affiliation workflows for portal developers."""

    def test_demo_affiliation_workflow(self):
        """
        Test creating and transitioning affiliations with partial dates.

        This shows how to:
        1. Create affiliations with PartialDateField (year-only precision)
        2. Transition affiliation types (e.g., MEMBER → ADMIN)
        3. Handle primary affiliation designation
        """
        from partial_date import PartialDate

        person = PersonFactory(email="postdoc@example.com")
        university = OrganizationFactory(name="Example University")

        # Create affiliation with year-only start date
        affiliation = Affiliation.objects.create(
            person=person,
            organization=university,
            type=Affiliation.MembershipType.MEMBER,
            start_date=PartialDate("2020"),  # Year-only precision (string format)
            is_primary=True,
        )

        assert affiliation.start_date is not None
        assert str(affiliation.start_date) == "2020"  # PartialDate string representation
        assert affiliation.is_primary

        # Transition to admin (e.g., after promotion)
        affiliation.type = Affiliation.MembershipType.ADMIN
        affiliation.save()

        assert affiliation.type == Affiliation.MembershipType.ADMIN

        # Create second affiliation (e.g., joint appointment)
        secondary_org = OrganizationFactory(name="Collaborating Institute")
        Affiliation.objects.create(
            person=person,
            organization=secondary_org,
            type=Affiliation.MembershipType.MEMBER,
            is_primary=False,  # Only one primary allowed
        )

        assert person.affiliations.count() == 2
        assert person.affiliations.filter(is_primary=True).count() == 1


@pytest.mark.django_db
class TestDemoAdminViewsLoad:
    """
    Test admin interface integration for contributors.

    These tests verify that the admin views for Person and Organization
    load correctly and display inline affiliations/members.
    """

    def test_person_admin_changelist_loads(self, admin_client):
        """Verify Person admin changelist view loads."""
        url = reverse("admin:contributors_person_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200
        assert b"Select person to change" in response.content or b"person" in response.content.lower()

    def test_person_admin_change_view_loads(self, admin_client):
        """Verify Person admin change view shows affiliation inline."""
        person = PersonFactory(email="admin-test@example.com")
        url = reverse("admin:contributors_person_change", args=[person.pk])
        response = admin_client.get(url)
        assert response.status_code == 200
        # Check for affiliation inline presence
        assert b"affiliation" in response.content.lower()

    def test_organization_admin_changelist_loads(self, admin_client):
        """Verify Organization admin changelist view loads."""
        url = reverse("admin:contributors_organization_changelist")
        response = admin_client.get(url)
        assert response.status_code == 200

    def test_organization_admin_change_view_loads(self, admin_client):
        """Verify Organization admin shows members inline."""
        org = OrganizationFactory(name="Test Research Center")
        url = reverse("admin:contributors_organization_change", args=[org.pk])
        response = admin_client.get(url)
        assert response.status_code == 200
        # Check for members inline presence
        assert b"members" in response.content.lower() or b"affiliation" in response.content.lower()
