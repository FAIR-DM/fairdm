"""Tests for the object-level permission backend that carries a model-level
permission held through a portal role down to individual records (FR-018,
FR-020).

``ModelBackend`` answers every object-level question with ``False``
(``django/contrib/auth/backends.py``), so a person holding ``change_dataset``
at the model level cannot in fact change a dataset until something derives
the object-level answer from it. See ``fairdm/portal_roles.py`` for how the
four shipped roles use this, and ``fairdm/core/permissions.py:44-53`` for the
``contributors.manage_organization`` exclusion this backend must also carry.
"""

import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType

from fairdm.contrib.contributors.models import Organization
from fairdm.factories import DatasetFactory, OrganizationFactory, PersonFactory
from fairdm.permissions import PortalRolePermissionBackend


def _permission(app_label, codename):
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)


@pytest.mark.django_db
class TestPortalRoleBackend:
    """FR-018, FR-020: an object-level question answered from model-level rights."""

    def test_a_model_level_permission_held_through_a_group_answers_for_any_instance(
        self,
    ):
        person = PersonFactory()
        group = Group.objects.create(name="Some Role")
        group.permissions.add(_permission("dataset", "change_dataset"))
        person.groups.add(group)
        dataset = DatasetFactory()

        assert person.has_perm("dataset.change_dataset", dataset)

    def test_a_person_without_the_permission_answers_false(self):
        person = PersonFactory()
        dataset = DatasetFactory()

        assert not person.has_perm("dataset.change_dataset", dataset)

    def test_a_permission_granted_directly_to_the_person_answers_the_same_way(self):
        person = PersonFactory()
        person.user_permissions.add(_permission("dataset", "change_dataset"))
        dataset = DatasetFactory()

        assert person.has_perm("dataset.change_dataset", dataset)

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
        person.user_permissions.add(_permission("dataset", "change_dataset"))
        organization = OrganizationFactory()

        assert not person.has_perm("contributors.change_organization", organization)

    def test_has_perm_with_no_object_answers_false_from_this_backend_directly(self):
        """The chain cannot recurse into this backend: it must answer ``False``
        on its own before ever asking ``user.has_perm(perm)`` again."""
        person = PersonFactory()
        person.user_permissions.add(_permission("dataset", "change_dataset"))
        backend = PortalRolePermissionBackend()

        assert backend.has_perm(person, "dataset.change_dataset", None) is False

    def test_manage_organization_is_never_answered_by_this_backend(self):
        """D14: a stale ``Permission`` row for it survives in migrated databases -
        the model no longer declares it (``fairdm/contrib/contributors/migrations/
        0017_remove_manage_organization_permission.py``), but an upgraded portal's
        row is never deleted - and this right comes from a current owner
        affiliation and nothing else (``fairdm/core/permissions.py:44-53``)."""
        person = PersonFactory()
        organization = OrganizationFactory()
        stale_permission, _ = Permission.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(Organization),
            codename="manage_organization",
            defaults={"name": "Can manage organization"},
        )
        person.user_permissions.add(stale_permission)

        assert not person.has_perm("contributors.manage_organization", organization)
