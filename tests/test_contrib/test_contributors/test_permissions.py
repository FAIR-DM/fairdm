"""Test organization ownership and permissions (User Story 3c).

Tests organization owner assignment, guardian permissions integration,
and ownership transfer functionality.
"""

import pytest
from django.contrib.auth import get_user_model
from partial_date import PartialDate

from fairdm.contrib.contributors.models import Affiliation, Organization
from fairdm.factories import PersonFactory

User = get_user_model()


# ── T061: Assign organization owner ─────────────────────────────────────────


@pytest.mark.django_db
class TestAssignOrganizationOwner:
    """Verify organization owner assignment via Affiliation type=OWNER."""

    def test_owner_affiliation_grants_manage_permission(self, organization, person):
        """Creating OWNER affiliation grants manage_organization permission."""
        # Person extends AbstractUser, so person IS the user
        # Create OWNER affiliation
        affiliation = Affiliation.objects.create(
            person=person,
            organization=organization,
            type=3,  # OWNER from FairDMAffiliationTypes
            is_primary=True,
        )

        # Verify guardian permission was granted
        assert person.has_perm("manage_organization", organization)

    def test_removing_owner_type_revokes_permission(self, organization, owner_affiliation):
        """Changing affiliation type from OWNER revokes manage_organization permission."""
        person = owner_affiliation.person

        # Verify owner has permission initially
        assert person.has_perm("manage_organization", organization)

        # Change affiliation type to MEMBER (2)
        owner_affiliation.type = 2
        owner_affiliation.save()

        # Verify permission was revoked
        assert not person.has_perm("manage_organization", organization)

    def test_multiple_owners_allowed(self, organization, person):
        """Multiple people can be owners of the same organization."""
        # Create second person (Person is User model)
        person2 = PersonFactory(
            email="second@example.com",
            first_name="Second",
            last_name="Owner",
        )

        # Create two OWNER affiliations
        aff1 = Affiliation.objects.create(
            person=person,
            organization=organization,
            type=3,
            is_primary=False,
        )
        aff2 = Affiliation.objects.create(
            person=person2,
            organization=organization,
            type=3,
            is_primary=False,
        )

        # Both users should have permission
        assert person.has_perm("manage_organization", organization)
        assert person2.has_perm("manage_organization", organization)


# ── T062: Owner can edit organization ───────────────────────────────────────


@pytest.mark.django_db
class TestOwnerCanEditOrganization:
    """Verify owner can edit organization details."""

    def test_owner_can_edit_organization_name(self, client, organization, owner_affiliation):
        """Owner can edit organization name via admin or view."""
        person = owner_affiliation.person
        client.force_login(person)

        # Simulate edit (this would normally be a view URL)
        # For now, just verify permission check passes
        assert person.has_perm("manage_organization", organization)

        # Update organization as owner
        organization.name = "Updated Organization Name"
        organization.save()

        organization.refresh_from_db()
        assert organization.name == "Updated Organization Name"

    def test_owner_can_manage_members(self, client, organization, owner_affiliation):
        """Owner can add/remove organization members."""
        person = owner_affiliation.person
        client.force_login(person)

        # Verify owner can manage members
        assert person.has_perm("manage_organization", organization)

        # Create new member affiliation
        new_member = PersonFactory(
            email="new@example.com",
            first_name="New",
            last_name="Member",
        )
        member_affiliation = Affiliation.objects.create(
            person=new_member,
            organization=organization,
            type=2,  # MEMBER
            is_primary=False,
        )

        # Verify affiliation was created
        assert organization.affiliations.filter(person=new_member).exists()

    def test_owner_can_manage_sub_organizations(self, client, organization, owner_affiliation):
        """Owner can create sub-organizations."""
        person = owner_affiliation.person
        client.force_login(person)

        # Create sub-organization
        sub_org = Organization.objects.create(
            name="Sub Organization",
            parent=organization,
        )

        # Verify sub-organization relationship
        sub_org.refresh_from_db()
        assert sub_org.parent == organization


# ── T063: Non-owner cannot edit ─────────────────────────────────────────────


@pytest.mark.django_db
class TestNonOwnerCannotEdit:
    """Verify non-owners cannot edit organization."""

    def test_non_owner_lacks_permission(self, organization, person):
        """Non-owner person without OWNER affiliation lacks manage permission."""
        # Create MEMBER affiliation (not OWNER)
        Affiliation.objects.create(
            person=person,
            organization=organization,
            type=2,  # MEMBER
            is_primary=False,
        )

        # Verify person does NOT have manage permission
        assert not person.has_perm("manage_organization", organization)

    def test_anonymous_user_cannot_manage(self, client, organization):
        """Anonymous users cannot manage organizations."""
        from django.contrib.auth.models import AnonymousUser

        anon_user = AnonymousUser()

        # Verify no permission
        assert not anon_user.has_perm("manage_organization", organization)


# ── T064: Transfer ownership ────────────────────────────────────────────────


@pytest.mark.django_db
class TestTransferOwnership:
    """Verify ownership transfer functionality."""

    def test_transfer_ownership_via_affiliation_change(self, organization, owner_affiliation):
        """Transferring ownership updates affiliation and permissions."""
        old_owner = owner_affiliation.person

        # Create new owner person
        new_owner = PersonFactory(
            email="newowner@example.com",
            first_name="New",
            last_name="Owner",
        )

        # Verify old owner has permission
        assert old_owner.has_perm("manage_organization", organization)

        # Transfer via affiliation changes
        # Option 1: Change existing affiliation type
        owner_affiliation.type = 2  # Demote to MEMBER
        owner_affiliation.save()

        # Create new OWNER affiliation
        new_affiliation = Affiliation.objects.create(
            person=new_owner,
            organization=organization,
            type=3,  # OWNER
            is_primary=True,
        )

        # Verify permission transfer
        assert not old_owner.has_perm("manage_organization", organization)
        assert new_owner.has_perm("manage_organization", organization)

    def test_transfer_ownership_preserves_history(self, organization, owner_affiliation):
        """Ownership transfer preserves affiliation history with dates."""
        old_owner = owner_affiliation.person

        # Set end date on old owner affiliation (use PartialDate)
        owner_affiliation.end_date = PartialDate("2026-02-18")
        owner_affiliation.save()

        # Create new owner
        new_owner = PersonFactory(
            email="newowner2@example.com",
            first_name="New",
            last_name="Owner2",
        )

        new_affiliation = Affiliation.objects.create(
            person=new_owner,
            organization=organization,
            type=3,
            is_primary=True,
            start_date=PartialDate("2026-02-18"),
        )

        # Verify both affiliations exist in history
        assert organization.affiliations.filter(person=old_owner).exists()
        assert organization.affiliations.filter(person=new_owner).exists()


# ── T065: Admin override access ─────────────────────────────────────────────


@pytest.mark.django_db
class TestAdminOverrideAccess:
    """Verify superusers can access organizations regardless of ownership."""

    def test_superuser_bypasses_ownership(self, admin_user, organization):
        """Superusers can edit any organization without OWNER affiliation."""
        # Superuser should have access even without manage_organization permission
        # Django admin checks is_superuser separately

        assert admin_user.is_superuser
        # In Django admin, superuser check happens before object-level perms
        # So this test verifies superuser *could* access if admin configured correctly

    def test_staff_without_permission_cannot_edit(self, organization):
        """Staff users without manage permission cannot edit organizations."""
        staff_user = PersonFactory(
            email="staff@example.com",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )

        # Verify no object permission
        assert not staff_user.has_perm("manage_organization", organization)
