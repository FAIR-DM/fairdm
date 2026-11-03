"""Tests for admin site access by rights-carrying roles."""

import pytest
from django.urls import reverse
from django.utils import translation

from fairdm.contrib.admin.sites import CustomAdminSite
from fairdm.contrib.identity.models import Identity
from fairdm.factories import PersonFactory
from fairdm.portal_roles import PortalRoles


@pytest.fixture(autouse=True)
def _reconciled_roles(db):
    PortalRoles.reconcile()


def _holder_of(role_name):
    from django.contrib.auth.models import Group

    person = PersonFactory(password="password")
    person.groups.add(Group.objects.get(name=role_name))
    return person


@pytest.mark.django_db
class TestAdministrationAccessForRoleHolders:
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


@pytest.mark.django_db
class TestAdministrationHeader:
    @pytest.fixture
    def identity(self, db):
        identity = Identity.get_solo()
        identity.set_current_language("en")
        identity.name = "Rock Portal"
        identity.description = "A portal"
        identity.save()
        return identity

    def _context_in_a_new_process(self, rf, admin_user):
        """Return the context of a site that never saw the identity being saved."""
        request = rf.get("/")
        request.user = admin_user
        return CustomAdminSite().each_context(request)

    def test_a_process_that_never_saved_the_identity_shows_the_portal_name(
        self, rf, admin_user, identity
    ):
        context = self._context_in_a_new_process(rf, admin_user)

        assert context["site_header"] == "Rock Portal"
        assert context["site_title"] == "Rock Portal"

    def test_the_name_follows_the_language_of_the_visitor(
        self, rf, admin_user, identity
    ):
        identity.set_current_language("de")
        identity.name = "Gesteinsportal"
        identity.description = "Ein Portal"
        identity.save()

        with translation.override("de"):
            german = self._context_in_a_new_process(rf, admin_user)
        with translation.override("en"):
            english = self._context_in_a_new_process(rf, admin_user)

        assert german["site_header"] == "Gesteinsportal"
        assert english["site_header"] == "Rock Portal"

    def test_a_portal_with_no_saved_name_keeps_the_default_heading(
        self, rf, admin_user
    ):
        context = self._context_in_a_new_process(rf, admin_user)

        assert context["site_header"] == CustomAdminSite.site_header
        assert context["site_title"] == CustomAdminSite.site_title
