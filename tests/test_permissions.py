"""Tests for the object-level permission backend that carries role permissions down to records."""

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType

from fairdm.contrib.contributors.models import Organization
from fairdm.factories import DatasetFactory, OrganizationFactory, PersonFactory
from fairdm.permissions import PortalRolePermissionBackend
from fairdm.portal_roles import PortalRoles


def _permission(app_label, codename):
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


@pytest.mark.django_db
class TestPortalRoleBackend:
    def test_a_model_level_permission_held_through_a_shipped_role_answers_for_any_instance(
        self,
    ):
        person = PersonFactory()
        group = Group.objects.get(name=PortalRoles.DATA_CURATOR.name)
        person.groups.add(group)
        dataset = DatasetFactory()

        assert person.has_perm("dataset.change_dataset", dataset)

    def test_a_person_without_the_permission_answers_false(self):
        person = PersonFactory()
        dataset = DatasetFactory()

        assert not person.has_perm("dataset.change_dataset", dataset)

    def test_a_permission_granted_directly_to_the_person_is_refused(self):
        person = PersonFactory()
        person.user_permissions.add(_permission("dataset", "change_dataset"))
        dataset = DatasetFactory()

        assert not person.has_perm("dataset.change_dataset", dataset)

    def test_a_permission_held_through_a_group_the_portal_invented_is_refused(self):
        person = PersonFactory()
        group = Group.objects.create(name="A Group The Portal Made Up")
        group.permissions.add(_permission("dataset", "change_dataset"))
        person.groups.add(group)
        dataset = DatasetFactory()

        assert not person.has_perm("dataset.change_dataset", dataset)

    def test_an_anonymous_user_answers_false(self):
        dataset = DatasetFactory()
        backend = PortalRolePermissionBackend()

        assert (
            backend.has_perm(AnonymousUser(), "dataset.change_dataset", dataset)
            is False
        )

    def test_a_deactivated_account_answers_false(self):
        person = PersonFactory(is_active=False)
        person.user_permissions.add(_permission("dataset", "change_dataset"))
        dataset = DatasetFactory()

        assert person.has_perm("dataset.change_dataset", dataset) is False

    def test_a_permission_held_for_one_model_does_not_answer_for_another(self):
        person = PersonFactory()
        group = Group.objects.get(name=PortalRoles.DATA_CURATOR.name)
        person.groups.add(group)
        organization = OrganizationFactory()

        assert not person.has_perm("contributors.change_organization", organization)

    def test_a_permission_string_with_no_app_label_answers_false_rather_than_raising(
        self,
    ):
        person = PersonFactory()
        dataset = DatasetFactory()

        assert person.has_perm("change_dataset", dataset) is False

    def test_has_perm_with_no_object_answers_false_from_this_backend_directly(self):
        # The backend must answer False itself, or the chain recurses into user.has_perm(perm).
        person = PersonFactory()
        person.user_permissions.add(_permission("dataset", "change_dataset"))
        backend = PortalRolePermissionBackend()

        assert backend.has_perm(person, "dataset.change_dataset", None) is False

    def test_registering_the_backend_does_not_break_authenticate(self):
        # authenticate() inspects each backend's `authenticate` signature, so a backend without that
        # method breaks sign-in for every user.
        from django.contrib.auth import authenticate

        assert authenticate(email="nobody@example.com", password="wrong") is None

    def test_manage_organization_is_never_answered_by_this_backend(self):
        # A stale Permission row survives in migrated databases, because the migration that removed the
        # permission never deleted rows.
        person = PersonFactory()
        organization = OrganizationFactory()
        stale_permission, _ = Permission.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Organization),
            codename="manage_organization",
            defaults={"name": "Can manage organization"},
        )
        person.user_permissions.add(stale_permission)

        assert not person.has_perm("contributors.manage_organization", organization)


@pytest.mark.django_db
class TestImportAndPublishGatePermissions:
    # The import and publish gates ask has_perm(f"{app_label}.import_data", instance), the dotted
    # spelling this backend requires. A bare codename is refused by design.
    def test_a_data_curator_is_admitted_to_import_on_a_dataset_they_did_not_create(
        self,
    ):
        curator = PersonFactory()
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
        dataset = DatasetFactory()

        assert curator.has_perm("dataset.import_data", dataset)

    def test_a_person_holding_nothing_is_refused_import(self):
        person = PersonFactory()
        dataset = DatasetFactory()

        assert not person.has_perm("dataset.import_data", dataset)

    def test_a_contributor_holding_the_object_level_row_is_admitted_to_import(self):
        from fairdm.core.utils import assign_perm

        contributor = PersonFactory()
        dataset = DatasetFactory()
        assign_perm("import_data", contributor, dataset)

        assert contributor.has_perm("dataset.import_data", dataset)

    def test_a_data_curator_is_admitted_to_publish_on_a_dataset_they_did_not_create(
        self,
    ):
        curator = PersonFactory()
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
        dataset = DatasetFactory()

        assert curator.has_perm("dataset.can_publish", dataset)

    def test_a_person_holding_nothing_is_refused_publish(self):
        person = PersonFactory()
        dataset = DatasetFactory()

        assert not person.has_perm("dataset.can_publish", dataset)

    def test_a_contributor_holding_the_object_level_row_is_admitted_to_publish(self):
        from fairdm.core.utils import assign_perm

        contributor = PersonFactory()
        dataset = DatasetFactory()
        assign_perm("can_publish", contributor, dataset)

        assert contributor.has_perm("dataset.can_publish", dataset)
