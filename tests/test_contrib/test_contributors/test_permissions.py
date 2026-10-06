"""Tests for organization ownership and permissions."""

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


@pytest.mark.django_db
class TestAssignOrganizationOwner:
    def test_owner_affiliation_grants_manage_permission(self, organization, person):
        affiliation = Affiliation.objects.create(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
            is_primary=True,
        )

        assert person.has_perm("manage_organization", organization)

    def test_removing_owner_type_revokes_permission(
        self, organization, owner_affiliation
    ):
        person = owner_affiliation.person

        assert person.has_perm("manage_organization", organization)

        owner_affiliation.refresh_from_db()
        owner_affiliation.type = Affiliation.MembershipType.MEMBER
        owner_affiliation.save()

        assert not person.has_perm("manage_organization", organization)

    def test_multiple_owners_allowed(self, organization, person):
        person2 = PersonFactory(
            email="second@example.com",
            first_name="Second",
            last_name="Owner",
        )

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

        person_fresh = Person.objects.get(pk=person.pk)
        person2_fresh = Person.objects.get(pk=person2.pk)

        assert person_fresh.has_perm("manage_organization", organization)
        assert person2_fresh.has_perm("manage_organization", organization)


@pytest.mark.django_db
class TestOwnershipIsScoped:
    def test_owner_of_one_organization_holds_nothing_on_another(self, person):
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


@pytest.mark.django_db
class TestOwnershipDemotion:
    def test_no_guardian_row_is_ever_written_across_promotion_and_demotion(
        self, organization, person
    ):
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


@pytest.mark.django_db
class TestOwnerCanEditOrganization:
    def test_owner_can_edit_organization_name(
        self, client, organization, owner_affiliation
    ):
        person = owner_affiliation.person
        client.force_login(person)

        assert person.has_perm("manage_organization", organization)

        organization.name = "Updated Organization Name"
        organization.save()

        organization.refresh_from_db()
        assert organization.name == "Updated Organization Name"

    def test_owner_can_manage_members(self, client, organization, owner_affiliation):
        person = owner_affiliation.person
        client.force_login(person)

        assert person.has_perm("manage_organization", organization)

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

        assert organization.affiliations.filter(person=new_member).exists()

    def test_owner_can_manage_sub_organizations(
        self, client, organization, owner_affiliation
    ):
        person = owner_affiliation.person
        client.force_login(person)

        sub_org = Organization.objects.create(
            name="Sub Organization",
            parent=organization,
        )

        sub_org.refresh_from_db()
        assert sub_org.parent == organization


@pytest.mark.django_db
class TestNonOwnerCannotEdit:
    def test_non_owner_lacks_permission(self, organization, person):
        Affiliation.objects.create(
            person=person,
            organization=organization,
            type=Affiliation.MembershipType.MEMBER,
            is_primary=False,
        )

        assert not person.has_perm("manage_organization", organization)

    def test_anonymous_user_cannot_manage(self, client, organization):
        from django.contrib.auth.models import AnonymousUser

        anon_user = AnonymousUser()

        assert not anon_user.has_perm("manage_organization", organization)


@pytest.mark.django_db
class TestTransferOwnership:
    def test_transfer_ownership_via_affiliation_change(
        self, organization, owner_affiliation
    ):
        old_owner = owner_affiliation.person

        new_owner = PersonFactory(
            email="newowner@example.com",
            first_name="New",
            last_name="Owner",
        )

        assert old_owner.has_perm("manage_organization", organization)

        owner_affiliation.refresh_from_db()
        owner_affiliation.type = Affiliation.MembershipType.MEMBER
        owner_affiliation.save()

        new_affiliation = Affiliation.objects.create(
            person=new_owner,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
            is_primary=True,
        )

        old_owner_fresh = Person.objects.get(pk=old_owner.pk)
        new_owner_fresh = Person.objects.get(pk=new_owner.pk)

        assert not old_owner_fresh.has_perm("manage_organization", organization)
        assert new_owner_fresh.has_perm("manage_organization", organization)

    def test_transfer_ownership_preserves_history(
        self, organization, owner_affiliation
    ):
        old_owner = owner_affiliation.person

        owner_affiliation.end_date = PartialDate("2026-02-18")
        owner_affiliation.save()

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

        assert organization.affiliations.filter(person=old_owner).exists()
        assert organization.affiliations.filter(person=new_owner).exists()

        # Preserving history is not enough on its own: the end date must also
        # end the rights the OWNER type would otherwise still confer.
        old_owner = Person.objects.get(pk=old_owner.pk)
        assert not old_owner.has_perm("contributors.manage_organization", organization)


@pytest.mark.django_db
class TestAdminOverrideAccess:
    def test_superuser_bypasses_ownership(self, admin_user, organization):

        assert admin_user.is_superuser

    def test_staff_without_permission_cannot_edit(self, organization):
        staff_user = PersonFactory(
            email="staff@example.com",
            first_name="Staff",
            last_name="User",
            is_staff=True,
        )

        assert not staff_user.has_perm("manage_organization", organization)


@pytest.mark.django_db
class TestDeactivatedOwner:
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


@pytest.mark.django_db
class TestEndedOwnershipRevokesPermission:
    def test_owner_affiliation_with_a_past_end_date_grants_nothing(
        self, organization, owner_affiliation
    ):
        person = owner_affiliation.person
        assert person.has_perm("manage_organization", organization)

        owner_affiliation.end_date = PartialDate("2020-01-01")
        owner_affiliation.save()

        person = Person.objects.get(pk=person.pk)
        assert not person.has_perm("manage_organization", organization)
        assert not person.has_perm("contributors.manage_organization", organization)


@pytest.mark.django_db
class TestStoredGuardianGrantNeverHonoured:
    def test_stored_grant_confers_nothing_without_an_owner_affiliation(
        self, organization, person
    ):
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
        assert superuser.has_perm("manage_organization", organization)
        assert superuser.has_perm("contributors.manage_organization", organization)


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
        curator = _holder_of(
            PortalRoles.DATA_CURATOR.name, email="curator2@example.com"
        )
        request = RequestFactory().get("/")
        request.user = curator

        assert can_open(Edit, request, sample) is True

    def test_the_record_carries_no_mark_saying_a_curator_changed_it(self):
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


VIEW, EDIT, MANAGE = 1, 2, 3
LEVELS = [VIEW, EDIT, MANAGE]
KINDS = ["project", "dataset", "sample", "measurement"]

#: What each level allows, from the permission table of the specification.
NEEDED = {
    "view_{}": VIEW,
    "add_{}": EDIT,
    "change_{}": EDIT,
    "change_{}_metadata": EDIT,
    "import_data": EDIT,
    "modify_metadata": EDIT,
    "delete_{}": MANAGE,
    "change_{}_settings": MANAGE,
    "add_contributor": MANAGE,
    "modify_contributor": MANAGE,
    "can_publish": MANAGE,
}
MODELS = {
    "project": "project.Project",
    "dataset": "dataset.Dataset",
    "sample": "sample.Sample",
    "measurement": "measurement.Measurement",
}


def permission_table(kind):
    """List ``(permission, level needed)`` for each permission the model declares."""
    from django.apps import apps

    meta = apps.get_model(MODELS[kind])._meta
    declared = [f"{action}_{kind}" for action in meta.default_permissions]
    declared += [codename for codename, _name in meta.permissions]
    needed = {template.format(kind): level for template, level in NEEDED.items()}
    return [(f"{kind}.{codename}", needed[codename]) for codename in declared]


def cases():
    return [
        (kind, level, perm, needed)
        for kind in KINDS
        for level in LEVELS
        for perm, needed in permission_table(kind)
    ]


@pytest.fixture
def holder(db):
    """A person who can sign in and is listed nowhere."""
    return PersonFactory(is_active=True, is_claimed=True, password="x")


def asked(user):
    """Return the user as the database holds them, so no cached answer is reused."""
    return Person.objects.get(pk=user.pk)


@pytest.mark.django_db
class TestRecordLevelBackend:
    @pytest.mark.parametrize(("kind", "level", "perm", "needed"), cases())
    def test_a_permission_is_granted_at_its_level_and_above_and_refused_below(
        self, record_chain, grant, holder, kind, level, perm, needed
    ):
        record = getattr(record_chain, kind)
        grant(record, holder, level)

        assert asked(holder).has_perm(perm, record) is (level >= needed)

    @pytest.mark.parametrize("kind", KINDS)
    def test_a_permission_the_table_does_not_know_is_refused(
        self, record_chain, grant, holder, kind
    ):
        record = getattr(record_chain, kind)
        grant(record, holder, MANAGE)

        assert not asked(holder).has_perm(f"{kind}.fly_{kind}", record)

    def test_a_registered_sample_type_answers_as_the_core_model(
        self, record_chain, grant, holder
    ):
        grant(record_chain.sample, holder, EDIT)
        person = asked(holder)

        assert person.has_perm("demo.view_rocksample", record_chain.sample)
        assert person.has_perm("demo.change_rocksample", record_chain.sample)
        assert not person.has_perm("demo.delete_rocksample", record_chain.sample)

    def test_a_registered_measurement_type_answers_as_the_core_model(
        self, record_chain, grant, holder
    ):
        grant(record_chain.measurement, holder, VIEW)
        person = asked(holder)

        assert person.has_perm("demo.view_examplemeasurement", record_chain.measurement)
        assert not person.has_perm(
            "demo.change_examplemeasurement", record_chain.measurement
        )

    def test_a_subtype_permission_naming_another_model_is_refused(
        self, record_chain, grant, holder
    ):
        grant(record_chain.sample, holder, MANAGE)

        assert not asked(holder).has_perm(
            "demo.view_examplemeasurement", record_chain.sample
        )

    def test_a_level_on_a_dataset_reaches_its_samples_and_measurements(
        self, record_chain, grant, holder
    ):
        grant(record_chain.other_dataset, holder, EDIT)
        person = asked(holder)

        assert person.has_perm(
            "measurement.change_measurement", record_chain.measurement
        )
        assert not person.has_perm("sample.view_sample", record_chain.sample)
        assert not person.has_perm("dataset.view_dataset", record_chain.dataset)

    def test_a_level_on_a_dataset_does_not_reach_the_project(
        self, record_chain, grant, holder
    ):
        grant(record_chain.dataset, holder, MANAGE)

        assert not asked(holder).has_perm("project.view_project", record_chain.project)

    def test_a_level_on_a_project_reaches_its_datasets_and_theirs(
        self, record_chain, grant, holder
    ):
        grant(record_chain.project, holder, EDIT)
        person = asked(holder)

        assert person.has_perm("dataset.change_dataset", record_chain.dataset)
        assert person.has_perm("sample.change_sample", record_chain.sample)
        assert person.has_perm(
            "measurement.change_measurement", record_chain.measurement
        )
        assert not person.has_perm(
            "measurement.delete_measurement", record_chain.measurement
        )

    def test_the_higher_of_two_levels_applies(self, record_chain, grant, holder):
        grant(record_chain.project, holder, MANAGE)
        grant(record_chain.dataset, holder, VIEW)

        assert asked(holder).has_perm("dataset.delete_dataset", record_chain.dataset)

    def test_a_person_listed_on_a_dataset_opens_it_and_not_a_private_project(
        self, record_chain, grant, holder
    ):
        from fairdm.utils.choices import Visibility

        record_chain.project.visibility = Visibility.PRIVATE
        record_chain.project.save()
        grant(record_chain.dataset, holder, VIEW)
        person = asked(holder)

        assert person.has_perm("dataset.view_dataset", record_chain.dataset)
        assert not person.has_perm("project.view_project", record_chain.project)

    @pytest.mark.parametrize("kind", KINDS)
    def test_a_stored_guardian_row_on_a_core_record_grants_nothing(
        self, record_chain, holder, kind
    ):
        from fairdm.core.utils import assign_perm

        record = getattr(record_chain, kind)
        assign_perm(f"{kind}.view_{kind}", holder, record)
        assign_perm(f"{kind}.change_{kind}", holder, record)

        person = asked(holder)
        assert not person.has_perm(f"{kind}.view_{kind}", record)
        assert not person.has_perm(f"{kind}.change_{kind}", record)

    def test_a_stored_guardian_row_on_a_dataset_no_longer_reaches_its_sample(
        self, record_chain, holder
    ):
        from fairdm.core.utils import assign_perm

        assign_perm("dataset.change_dataset", holder, record_chain.dataset)

        assert not asked(holder).has_perm("sample.change_sample", record_chain.sample)

    def test_a_stored_guardian_row_still_works_on_an_organization(
        self, organization, holder
    ):
        from guardian.shortcuts import assign_perm as guardian_assign_perm

        guardian_assign_perm("contributors.change_organization", holder, organization)

        assert asked(holder).has_perm("contributors.change_organization", organization)

    def test_an_organizations_members_and_owner_gain_nothing(
        self, record_chain, holder
    ):
        from fairdm.factories import OrganizationFactory

        organization = OrganizationFactory()
        Affiliation.objects.create(
            person=holder,
            organization=organization,
            type=Affiliation.MembershipType.OWNER,
            is_primary=True,
        )
        from fairdm.contrib.contributors.services.crediting import Crediting

        Crediting(record_chain.dataset).add(organization)

        assert not asked(holder).has_perm("dataset.view_dataset", record_chain.dataset)

    def test_a_person_listed_with_no_level_is_granted_nothing(
        self, record_chain, grant, holder
    ):
        grant(record_chain.dataset, holder, None)

        assert not asked(holder).has_perm("dataset.view_dataset", record_chain.dataset)

    def test_an_inactive_user_is_refused(self, record_chain, grant, holder):
        grant(record_chain.dataset, holder, MANAGE)
        holder.is_active = False
        holder.save()

        assert not asked(holder).has_perm("dataset.view_dataset", record_chain.dataset)

    def test_a_visitor_is_refused(self, record_chain):
        from django.contrib.auth.models import AnonymousUser

        assert not AnonymousUser().has_perm(
            "dataset.view_dataset", record_chain.dataset
        )

    def test_a_question_with_no_record_is_left_to_the_other_backends(
        self, record_chain, grant, holder
    ):
        from fairdm.contrib.contributors.permissions import RecordLevelBackend

        grant(record_chain.dataset, holder, MANAGE)

        assert RecordLevelBackend().has_perm(holder, "dataset.view_dataset") is False
        assert not asked(holder).has_perm("dataset.view_dataset")

    def test_a_question_about_a_person_is_left_to_the_other_backends(self, holder):
        from fairdm.contrib.contributors.permissions import RecordLevelBackend

        assert (
            RecordLevelBackend().has_perm(holder, "contributors.view_person", holder)
            is False
        )

    def test_a_portal_role_is_unchanged(self, record_chain):
        curator = _holder_of("Data Curator", email="curator-us4@example.com")

        assert curator.has_perm("dataset.change_dataset", record_chain.dataset)
        assert curator.has_perm("dataset.view_dataset", record_chain.dataset)


@pytest.mark.django_db
class TestObjectPermissionsSurvive:
    def test_organization_grant_still_resolves(self, user):
        from fairdm.factories import OrganizationFactory

        organization = OrganizationFactory()
        assign_perm("view_organization", user, organization)

        assert user.has_perm("contributors.view_organization", organization) is True
