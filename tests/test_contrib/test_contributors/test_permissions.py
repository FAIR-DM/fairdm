"""Test organization ownership and permissions (User Story 3c).

Tests organization owner assignment, derived permissions via OrganizationPermissionBackend,
and ownership transfer functionality.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse
from guardian.shortcuts import assign_perm
from partial_date import PartialDate

from fairdm.contrib.contributors.models import Affiliation, Organization, Person
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
            type=Affiliation.MembershipType.OWNER,
            is_primary=True,
        )

        # Verify guardian permission was granted
        assert person.has_perm("manage_organization", organization)

    def test_removing_owner_type_revokes_permission(
        self, organization, owner_affiliation
    ):
        """Changing affiliation type from OWNER revokes manage_organization permission."""
        person = owner_affiliation.person

        # Verify owner has permission initially
        assert person.has_perm("manage_organization", organization)

        # Change affiliation type to MEMBER
        owner_affiliation.refresh_from_db()  # Ensure lifecycle hooks work properly
        owner_affiliation.type = Affiliation.MembershipType.MEMBER
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
            type=Affiliation.MembershipType.OWNER,
            is_primary=False,
        )
        aff2 = Affiliation.objects.create(
            person=person2,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
            is_primary=False,
        )

        # Get fresh instances from DB
        person_fresh = Person.objects.get(pk=person.pk)
        person2_fresh = Person.objects.get(pk=person2.pk)

        # Both users should have permission (derived from OWNER affiliation)
        assert person_fresh.has_perm("manage_organization", organization)
        assert person2_fresh.has_perm("manage_organization", organization)


# ── T078: Ownership is scoped to the organisation it was granted on ─────────


@pytest.mark.django_db
class TestOwnershipIsScoped:
    """Verify an owner membership confers rights on that organisation only (FR-026)."""

    def test_owner_of_one_organization_holds_nothing_on_another(self, person):
        """Owning organisation A grants no rights over unrelated organisation B."""
        from fairdm.factories import OrganizationFactory

        owned_org = OrganizationFactory(name="Owned University")
        other_org = OrganizationFactory(name="Unrelated University")

        Affiliation.objects.create(
            person=person,
            organization=owned_org,
            type=Affiliation.MembershipType.OWNER,
            is_primary=True,
        )

        assert person.has_perm("manage_organization", owned_org)
        assert not person.has_perm("manage_organization", other_org)


# ── T079: Demotion withdraws the right with no stored permission row ────────


@pytest.mark.django_db
class TestOwnershipDemotion:
    """Verify the management right is derived, never stored (FR-027).

    ``test_removing_owner_type_revokes_permission`` above already covers the
    right being withdrawn on demotion; this class adds the clause that test
    does not: at no point — owner or demoted — does a guardian object
    permission row exist for the organisation.
    """

    def test_no_guardian_row_is_ever_written_across_promotion_and_demotion(
        self, organization, person
    ):
        """No UserObjectPermission row exists while owner, nor after demotion."""
        from guardian.models import UserObjectPermission

        def guardian_rows_for_organization():
            content_type = ContentType.objects.get_for_model(Organization)
            return UserObjectPermission.objects.filter(
                content_type=content_type, object_pk=str(organization.pk)
            )

        affiliation = Affiliation.objects.create(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
            is_primary=True,
        )

        assert person.has_perm("manage_organization", organization)
        assert not guardian_rows_for_organization().exists()

        affiliation.type = Affiliation.MembershipType.MEMBER
        affiliation.save()

        assert not person.has_perm("manage_organization", organization)
        assert not guardian_rows_for_organization().exists()


# ── T062: Owner can edit organization ───────────────────────────────────────


@pytest.mark.django_db
class TestOwnerCanEditOrganization:
    """Verify owner can edit organization details."""

    def test_owner_can_edit_organization_name(
        self, client, organization, owner_affiliation
    ):
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
            type=Affiliation.MembershipType.MEMBER,
            is_primary=False,
        )

        # Verify affiliation was created
        assert organization.affiliations.filter(person=new_member).exists()

    def test_owner_can_manage_sub_organizations(
        self, client, organization, owner_affiliation
    ):
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
            type=Affiliation.MembershipType.MEMBER,
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

    def test_transfer_ownership_via_affiliation_change(
        self, organization, owner_affiliation
    ):
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
        owner_affiliation.refresh_from_db()  # Ensure lifecycle hooks work properly
        owner_affiliation.type = Affiliation.MembershipType.MEMBER  # Demote to MEMBER
        owner_affiliation.save()

        # Create new OWNER affiliation
        new_affiliation = Affiliation.objects.create(
            person=new_owner,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
            is_primary=True,
        )

        # Get fresh instances from DB
        old_owner_fresh = Person.objects.get(pk=old_owner.pk)
        new_owner_fresh = Person.objects.get(pk=new_owner.pk)

        # Verify permission transfer (derived from current affiliation state)
        assert not old_owner_fresh.has_perm("manage_organization", organization)
        assert new_owner_fresh.has_perm("manage_organization", organization)

    def test_transfer_ownership_preserves_history(
        self, organization, owner_affiliation
    ):
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
            type=Affiliation.MembershipType.OWNER,
            is_primary=True,
            start_date=PartialDate("2026-02-18"),
        )

        # Verify both affiliations exist in history
        assert organization.affiliations.filter(person=old_owner).exists()
        assert organization.affiliations.filter(person=new_owner).exists()

        # Preserving history is not enough on its own: the end date must also
        # end the rights the OWNER type would otherwise still confer (Defect A).
        old_owner = Person.objects.get(pk=old_owner.pk)
        assert not old_owner.has_perm("contributors.manage_organization", organization)


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


@pytest.mark.django_db
class TestDeactivatedOwner:
    """A deactivated account holds no rights.

    Management of an organization is worked out from the affiliation at the moment it
    is checked rather than stored, so deactivating an account has to be enough on its
    own to end that person's control of the organization. Every other backend in the
    chain refuses a deactivated account, and a check is granted if any single backend
    allows it, so this one has to refuse as well or deactivation stops meaning anything
    for organizations.
    """

    def test_deactivated_owner_cannot_manage_the_organization(
        self, organization, owner_affiliation
    ):
        person = owner_affiliation.person
        assert person.has_perm("manage_organization", organization)

        person.is_active = False
        person.save(update_fields=["is_active"])

        person = Person.objects.get(pk=person.pk)
        assert not person.has_perm("manage_organization", organization)
        assert not person.has_perm("contributors.manage_organization", organization)

    def test_reactivating_restores_management(self, organization, owner_affiliation):
        person = owner_affiliation.person
        person.is_active = False
        person.save(update_fields=["is_active"])

        person.is_active = True
        person.save(update_fields=["is_active"])

        person = Person.objects.get(pk=person.pk)
        assert person.has_perm("manage_organization", organization)


# ── Defect A: an ended OWNER affiliation confers no rights ─────────────────


@pytest.mark.django_db
class TestEndedOwnershipRevokesPermission:
    """Setting end_date on an OWNER affiliation ends the rights it conferred.

    ``Affiliation.end_date``'s help_text documents this: "Leave blank for
    active affiliations." An administrator who offboards a departing owner
    by setting the end date and leaving the type alone must actually revoke
    the right, not merely record history.
    """

    def test_owner_affiliation_with_a_past_end_date_grants_nothing(
        self, organization, owner_affiliation
    ):
        """An OWNER affiliation with end_date in the past fails has_perm."""
        person = owner_affiliation.person
        assert person.has_perm("manage_organization", organization)

        owner_affiliation.end_date = PartialDate("2020-01-01")
        owner_affiliation.save()

        person = Person.objects.get(pk=person.pk)
        assert not person.has_perm("manage_organization", organization)
        assert not person.has_perm("contributors.manage_organization", organization)


# ── Defect B: a stored guardian grant never confers manage_organization ────


@pytest.mark.django_db
class TestStoredGuardianGrantNeverHonoured:
    """A stored object-level ``manage_organization`` grant confers nothing.

    ``manage_organization`` was declared in one migration, its guardian rows
    removed in another, and the declaration dropped from
    ``Organization.Meta.permissions`` in a third - but Django never deletes
    the underlying ``Permission`` row when a permission leaves a model's
    options, so a database migrated forward can still carry it, and a
    guardian object-level grant can still be written against it. The
    derived affiliation rule and superuser status are the only two sources
    of this right; a stored row must never be honoured.
    """

    def test_stored_grant_confers_nothing_without_an_owner_affiliation(
        self, organization, person
    ):
        """A guardian UserObjectPermission row alone does not pass has_perm."""
        org_ct = ContentType.objects.get_for_model(Organization)
        Permission.objects.get_or_create(
            content_type=org_ct,
            codename="manage_organization",
            defaults={"name": "Can manage organization"},
        )
        assign_perm("manage_organization", person, organization)

        person = Person.objects.get(pk=person.pk)
        assert not person.has_perm("manage_organization", organization)
        assert not person.has_perm("contributors.manage_organization", organization)

    def test_superuser_still_passes_with_no_affiliation_or_stored_grant(
        self, organization, superuser
    ):
        """A superuser passes on affiliation-derived status alone, not a stored row."""
        assert superuser.has_perm("manage_organization", organization)
        assert superuser.has_perm("contributors.manage_organization", organization)


# ── T017: a role decides what its holder can actually do on the portal's own pages ──


def _holder_of(*role_names, email):
    from django.contrib.auth.models import Group

    from fairdm.portal_roles import PortalRoles

    PortalRoles.reconcile()
    person = PersonFactory(email=email, is_active=True)
    for role_name in role_names:
        person.groups.add(Group.objects.get(name=role_name))
    return person


@pytest.mark.django_db
class TestDataCuratorPortalPages:
    """FR-003, FR-007, FR-021: a Data Curator reaches another team's dataset - private
    included - and its samples through the portal's own pages, and the record carries no
    mark saying a curator changed it."""

    def _private_dataset_with_sample(self):
        from demo.factories import RockSampleFactory

        from fairdm.factories import DatasetFactory
        from fairdm.utils.choices import Visibility

        dataset = DatasetFactory(visibility=Visibility.PRIVATE)
        sample = RockSampleFactory(dataset=dataset)
        return dataset, sample

    def test_can_view_and_change_another_teams_private_dataset(self, client):
        from fairdm.portal_roles import PortalRoles

        dataset, _sample = self._private_dataset_with_sample()
        curator = _holder_of(PortalRoles.DATA_CURATOR.name, email="curator@example.com")

        assert curator.has_perm("dataset.view_dataset", dataset)
        assert curator.has_perm("dataset.change_dataset", dataset)

        client.force_login(curator)
        response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )
        assert response.status_code == 200

    def test_can_view_and_change_the_datasets_sample(self):
        from fairdm.contrib.plugins.access import can_open
        from fairdm.core.sample.plugins import Edit
        from fairdm.portal_roles import PortalRoles

        _dataset, sample = self._private_dataset_with_sample()
        curator = _holder_of(PortalRoles.DATA_CURATOR.name, email="curator2@example.com")
        request = RequestFactory().get("/")
        request.user = curator

        assert can_open(Edit, request, sample) is True

    # No test exercises `DataImportView.check`/`DatasetPublishConfirm.check` here (the
    # "import and publish plugin pages" of this task's acceptance): `fairdm.contrib.
    # import_export.views` fails to import on its own, independent of this story
    # (`ImportError: cannot import name 'FairDMModelFormMixin' from 'fairdm.views'`) -
    # confirmed by attempting exactly that import in isolation. Flagged in
    # `decisions.md`/`concerns` rather than fixed: an unrelated pre-existing defect, not
    # named in any task this story assigns.

    def test_the_record_carries_no_mark_saying_a_curator_changed_it(self):
        """FR-021: met by writing no such mark. Pinned as a standing proof, not a probe of a
        mechanism that exists - there is nothing to mutate."""
        from fairdm.core.dataset.models import Dataset

        field_names = {field.name for field in Dataset._meta.get_fields()}
        assert not field_names & {
            "last_edited_by",
            "edited_by",
            "modified_by",
            "changed_by",
        }


@pytest.mark.django_db
class TestCommunityManagerPortalRights:
    """FR-004: a Community Manager changes a person and an organisation, cannot change a
    dataset, and cannot delete a person."""

    def test_can_change_a_person_and_an_organisation(self, organization):
        from fairdm.portal_roles import PortalRoles

        manager = _holder_of(
            PortalRoles.COMMUNITY_MANAGER.name, email="manager@example.com"
        )
        other_person = PersonFactory(email="managed@example.com")

        assert manager.has_perm("contributors.change_person", other_person)
        assert manager.has_perm("contributors.change_organization", organization)

    def test_cannot_change_a_dataset(self):
        from fairdm.factories import DatasetFactory
        from fairdm.portal_roles import PortalRoles

        manager = _holder_of(
            PortalRoles.COMMUNITY_MANAGER.name, email="manager2@example.com"
        )
        dataset = DatasetFactory()

        assert not manager.has_perm("dataset.change_dataset", dataset)

    def test_cannot_delete_a_person(self):
        from fairdm.portal_roles import PortalRoles

        manager = _holder_of(
            PortalRoles.COMMUNITY_MANAGER.name, email="manager3@example.com"
        )
        other_person = PersonFactory(email="managed2@example.com")

        assert not manager.has_perm("contributors.delete_person", other_person)


@pytest.mark.django_db
class TestAPersonHoldingTwoRolesHoldsBothSets:
    def test_holds_both_data_curator_and_community_manager_rights(self, organization):
        from fairdm.factories import DatasetFactory
        from fairdm.portal_roles import PortalRoles

        person = _holder_of(
            PortalRoles.DATA_CURATOR.name,
            PortalRoles.COMMUNITY_MANAGER.name,
            email="both-roles@example.com",
        )
        dataset = DatasetFactory()
        other_person = PersonFactory(email="managed3@example.com")

        assert person.has_perm("dataset.change_dataset", dataset)
        assert person.has_perm("contributors.change_person", other_person)
        assert person.has_perm("contributors.change_organization", organization)
