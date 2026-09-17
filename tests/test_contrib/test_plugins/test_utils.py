"""``check_has_edit_permission`` (T018, FR-019): a rights decision made by asking the
permission system, not by matching a group's name.
"""

import pytest
from django.test import RequestFactory

from fairdm.contrib.plugins.utils import check_has_edit_permission
from fairdm.factories import DatasetFactory, PersonFactory
from fairdm.portal_roles import PortalRoles


def _request_for(user):
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestCheckHasEditPermission:
    def test_a_superuser_is_admitted(self):
        superuser = PersonFactory(is_superuser=True, is_staff=True)
        dataset = DatasetFactory()

        assert check_has_edit_permission(_request_for(superuser), dataset) is True

    def test_the_instance_itself_is_admitted(self):
        person = PersonFactory()

        assert check_has_edit_permission(_request_for(person), person) is True

    def test_belonging_to_a_group_named_data_administrators_grants_nothing_on_its_own(self):
        """FR-019: the rights decision is made by asking the permission system, not by
        matching a group's name. A group carrying that literal name but none of the
        model's permissions must not admit its member - proving the removed branch is
        gone, independent of any portal role."""
        from django.contrib.auth.models import Group

        legacy_named_group = Group.objects.create(name="Data Administrators")
        member = PersonFactory()
        member.groups.add(legacy_named_group)
        dataset = DatasetFactory()

        assert not check_has_edit_permission(_request_for(member), dataset)

    def test_a_data_curator_is_admitted_through_the_permission_question_alone(self):
        from django.contrib.auth.models import Group

        PortalRoles.reconcile()
        curator = PersonFactory()
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
        dataset = DatasetFactory()

        assert check_has_edit_permission(_request_for(curator), dataset) is True

    def test_a_person_with_no_rights_is_refused(self):
        person = PersonFactory()
        dataset = DatasetFactory()

        assert not check_has_edit_permission(_request_for(person), dataset)
