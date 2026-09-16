"""The administration interface accepts a holder of a rights-carrying role (FR-006, FR-008).

Reaching the administration interface used to ask for ``is_staff`` alone, which no portal role
sets (research R3) - access is derived from role membership, never stored on the person.
"""

import pytest
from django.urls import reverse

from fairdm.factories import PersonFactory
from fairdm.portal_roles import PortalRoles


@pytest.fixture(autouse=True)
def _reconciled_roles(db):
    """Every test in this module needs the four shipped roles installed."""
    PortalRoles.reconcile()


def _holder_of(role_name):
    from django.contrib.auth.models import Group

    person = PersonFactory(password="password")
    person.groups.add(Group.objects.get(name=role_name))
    return person


@pytest.mark.django_db
class TestAdministrationAccessForRoleHolders:
    """A holder of each rights-carrying role reaches the index and a changelist, both with
    an existing session and by signing in through the administration login form."""

    @pytest.mark.parametrize(
        "role_name,changelist_url_name",
        [
            (
                PortalRoles.PORTAL_ADMINISTRATOR.name,
                "admin:contributors_person_changelist",
            ),
            (PortalRoles.DATA_CURATOR.name, "admin:dataset_dataset_changelist"),
            (
                PortalRoles.COMMUNITY_MANAGER.name,
                "admin:contributors_person_changelist",
            ),
        ],
    )
    def test_a_role_holder_reaches_the_index_and_a_changelist_with_an_existing_session(
        self, client, role_name, changelist_url_name
    ):
        holder = _holder_of(role_name)
        client.force_login(holder)

        index_response = client.get(reverse("admin:index"))
        changelist_response = client.get(reverse(changelist_url_name))

        assert index_response.status_code == 200
        assert changelist_response.status_code == 200

    @pytest.mark.parametrize(
        "role_name,changelist_url_name",
        [
            (
                PortalRoles.PORTAL_ADMINISTRATOR.name,
                "admin:contributors_person_changelist",
            ),
            (PortalRoles.DATA_CURATOR.name, "admin:dataset_dataset_changelist"),
            (
                PortalRoles.COMMUNITY_MANAGER.name,
                "admin:contributors_person_changelist",
            ),
        ],
    )
    def test_a_role_holder_reaches_the_index_and_a_changelist_by_signing_in(
        self, client, role_name, changelist_url_name
    ):
        holder = _holder_of(role_name)

        login_response = client.post(
            reverse("admin:login"),
            {"username": holder.email, "password": "password"},
            follow=True,
        )
        changelist_response = client.get(reverse(changelist_url_name))

        assert login_response.status_code == 200
        assert login_response.wsgi_request.user.is_authenticated
        assert changelist_response.status_code == 200

    def test_a_developer_only_holder_is_refused(self, client):
        holder = _holder_of(PortalRoles.DEVELOPER.name)
        client.force_login(holder)

        response = client.get(reverse("admin:index"))

        assert response.status_code == 302

    def test_an_ordinary_contributor_is_refused(self, client):
        person = PersonFactory(password="password")
        client.force_login(person)

        response = client.get(reverse("admin:index"))

        assert response.status_code == 302

    def test_a_deactivated_role_holder_is_refused(self, client):
        holder = _holder_of(PortalRoles.PORTAL_ADMINISTRATOR.name)
        holder.is_active = False
        holder.save()
        client.force_login(holder)

        response = client.get(reverse("admin:index"))

        assert response.status_code == 302
