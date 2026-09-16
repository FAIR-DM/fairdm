"""The administration interface's own explanation of FR-012/FR-013 (T022, research R6).

A raising ``pre_delete``/``pre_save`` receiver (T021) is the enforcement and holds for every
ORM writer, but it cannot explain itself: reached through the administration interface it
would surface as a server error. This module covers the ``Group`` administration class that
turns that into something the person who clicked can read - no delete action or button for a
shipped role, and a field error naming the role rather than a 500 when its name is changed.
"""

import pytest
from django.urls import reverse

from fairdm.portal_roles import PortalRoles


@pytest.fixture(autouse=True)
def _reconciled_roles(db):
    """Every test in this module needs the four shipped roles installed."""
    PortalRoles.reconcile()


@pytest.fixture
def shipped_group():
    from django.contrib.auth.models import Group

    return Group.objects.get(name=PortalRoles.DATA_CURATOR.name)


@pytest.mark.django_db
class TestShippedRoleDeleteProtection:
    def test_no_delete_button_on_the_change_form(self, admin_client, shipped_group):
        url = reverse("admin:auth_group_change", args=[shipped_group.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "deletelink" not in response.content.decode()

    def test_the_delete_view_itself_refuses(self, admin_client, shipped_group):
        url = reverse("admin:auth_group_delete", args=[shipped_group.pk])
        response = admin_client.get(url)

        assert response.status_code == 403

    def test_bulk_delete_action_does_not_remove_a_shipped_role(
        self, admin_client, shipped_group
    ):
        from django.contrib.auth.models import Group

        url = reverse("admin:auth_group_changelist")
        response = admin_client.post(
            url,
            {
                "action": "delete_selected",
                "_selected_action": [str(shipped_group.pk)],
            },
        )

        assert response.status_code == 200
        assert Group.objects.filter(pk=shipped_group.pk).exists()

    def test_delete_button_present_for_a_group_the_portal_made_itself(
        self, admin_client
    ):
        from django.contrib.auth.models import Group

        custom = Group.objects.create(name="Project Alpha Team")

        url = reverse("admin:auth_group_change", args=[custom.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        assert "deletelink" in response.content.decode()


@pytest.mark.django_db
class TestShippedRoleRenameProtection:
    def test_renaming_through_the_change_form_is_a_field_error_not_a_500(
        self, admin_client, shipped_group
    ):
        url = reverse("admin:auth_group_change", args=[shipped_group.pk])

        response = admin_client.post(url, {"name": "Data Custodian"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "FairDM requires" in content
        assert PortalRoles.DATA_CURATOR.name in content
        shipped_group.refresh_from_db()
        assert shipped_group.name == PortalRoles.DATA_CURATOR.name

    def test_resaving_a_shipped_role_with_its_name_unchanged_succeeds(
        self, admin_client, shipped_group
    ):
        url = reverse("admin:auth_group_change", args=[shipped_group.pk])

        response = admin_client.post(url, {"name": shipped_group.name})

        assert response.status_code == 302

    def test_a_group_the_portal_made_itself_renames_normally(self, admin_client):
        from django.contrib.auth.models import Group

        custom = Group.objects.create(name="Project Alpha Team")
        url = reverse("admin:auth_group_change", args=[custom.pk])

        response = admin_client.post(url, {"name": "Project Alpha Squad"})

        assert response.status_code == 302
        custom.refresh_from_db()
        assert custom.name == "Project Alpha Squad"


@pytest.mark.django_db
class TestShippedRoleDeleteMessage:
    """SPC-001/FR-012: the refusal names the role rather than a bare 403 - the
    naming message lives on the pre_delete receiver alone (T022/research R6), which the
    administration interface's own delete route never reaches (has_delete_permission
    returns False first, so Django raises PermissionDenied before it)."""

    def test_the_delete_page_names_the_role_and_says_fairdm_requires_it(
        self, admin_client, shipped_group
    ):
        url = reverse("admin:auth_group_delete", args=[shipped_group.pk])

        response = admin_client.get(url)

        assert response.status_code == 403
        content = response.content.decode()
        assert "FairDM requires" in content
        assert PortalRoles.DATA_CURATOR.name in content

    def test_posting_to_the_delete_page_also_names_the_role(
        self, admin_client, shipped_group
    ):
        from django.contrib.auth.models import Group

        url = reverse("admin:auth_group_delete", args=[shipped_group.pk])

        response = admin_client.post(url)

        assert response.status_code == 403
        assert "FairDM requires" in response.content.decode()
        assert Group.objects.filter(pk=shipped_group.pk).exists()

    def test_a_group_the_portal_made_itself_still_gets_the_ordinary_confirmation_page(
        self, admin_client
    ):
        from django.contrib.auth.models import Group

        custom = Group.objects.create(name="Project Alpha Team")
        url = reverse("admin:auth_group_delete", args=[custom.pk])

        response = admin_client.get(url)

        assert response.status_code == 200
