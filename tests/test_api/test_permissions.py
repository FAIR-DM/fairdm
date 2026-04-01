"""Permission enforcement tests for FairDM API (Feature 011 — US4).

Covers:
- Full permission matrix: anonymous / authenticated-no-perm / with-guardian-perm
  across list-public, list-private, detail-public, detail-private, create,
  update, and delete scenarios.
- Non-disclosure: private objects return 404 (not 403) to users without view perm.
- Cascading: users with guardian permissions can read/write permitted private objects.

These tests rely on ``guardian.shortcuts.assign_perm`` to set up per-object
permissions without seeding full Django model-level permissions.
"""

import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_token_client(user) -> APIClient:
    """Return an APIClient authenticated as *user* via token."""
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


# ---------------------------------------------------------------------------
# Anonymous access (read-only, public data)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAnonymousAccess:
    """Anonymous users can read public objects and nothing else."""

    def test_list_returns_200(self):
        response = APIClient().get(reverse("project-list"))
        assert response.status_code == 200

    def test_public_project_detail_returns_200(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().get(url).status_code == 200

    def test_private_project_detail_returns_404(self):
        """Non-disclosure: private project must return 404 to anonymous users."""
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().get(url).status_code == 404

    def test_post_returns_401(self):
        """Anonymous write must return 401 (not 403)."""
        response = APIClient().post(reverse("project-list"), {"name": "X"}, format="json")
        assert response.status_code == 401

    def test_patch_public_project_returns_401(self):
        """Anonymous PATCH must return 401."""
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        response = APIClient().patch(url, {"name": "Hacked"}, format="json")
        assert response.status_code == 401

    def test_delete_public_project_returns_401(self):
        """Anonymous DELETE must return 401."""
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().delete(url).status_code == 401


# ---------------------------------------------------------------------------
# Authenticated user — no guardian permissions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAuthenticatedNoPermission:
    """Authenticated users without guardian permissions on a specific object."""

    def test_private_project_detail_returns_404(self):
        """Non-disclosure: authenticated user with no view perm gets 404."""
        owner = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # different user, no perms
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        assert client.get(url).status_code == 404

    def test_patch_public_project_returns_403(self):
        """Authenticated user without change perm on PUBLIC project gets 403."""
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        client = make_token_client(UserFactory())  # no guardian perm
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        response = client.patch(url, {"name": "Hijack"}, format="json")
        assert response.status_code == 403

    def test_patch_private_project_returns_404(self):
        """Authenticated user without any perm on PRIVATE project gets 404."""
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # no guardian perm
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        response = client.patch(url, {"name": "Hijack"}, format="json")
        assert response.status_code == 404

    def test_delete_private_project_returns_404(self):
        """Authenticated user without any perm on PRIVATE project DELETE → 404."""
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        assert client.delete(url).status_code == 404

    def test_create_project_succeeds(self):
        """Any authenticated user can create a project (permissions assigned on creation)."""
        client = make_token_client(UserFactory())
        response = client.post(reverse("project-list"), {"name": "My New Project"}, format="json")
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# Authenticated user — with guardian permissions
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAuthenticatedWithPermission:
    """Authenticated users that have been explicitly granted guardian permissions."""

    def test_view_perm_allows_private_project_read(self):
        """User with guardian view_project on a private project can read it."""
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        client = make_token_client(user)
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        assert client.get(url).status_code == 200

    def test_change_perm_allows_patch(self):
        """User with guardian change_project on a project can PATCH it."""
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        assign_perm("change_project", user, proj)
        client = make_token_client(user)
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        resp = client.patch(url, {"name": "Updated"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_delete_perm_allows_delete(self):
        """User with guardian delete_project on a project can DELETE it."""
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        assign_perm("delete_project", user, proj)
        client = make_token_client(user)
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        assert client.delete(url).status_code == 204

    def test_owner_created_object_gets_full_access(self):
        """Object created via POST has guardian permissions auto-assigned to creator."""
        user = UserFactory()
        client = make_token_client(user)

        post_resp = client.post(reverse("project-list"), {"name": "Owner Project"}, format="json")
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]
        url = reverse("project-detail", kwargs={"uuid": uuid})

        # Owner can PATCH
        patch_resp = client.patch(url, {"name": "Renamed"}, format="json")
        assert patch_resp.status_code == 200

        # Owner can DELETE
        del_resp = client.delete(url)
        assert del_resp.status_code == 204

    def test_viewer_cannot_patch_private_project(self):
        """User with only view_project cannot PATCH — returns 403 (they can see it)."""
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)  # view but not change
        client = make_token_client(user)
        url = reverse("project-detail", kwargs={"uuid": proj.uuid})
        resp = client.patch(url, {"name": "No Access"}, format="json")
        assert resp.status_code == 403

    def test_private_project_appears_in_list_for_permitted_user(self):
        """User with view_project sees private project in list endpoint."""
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        client = make_token_client(user)
        response = client.get(reverse("project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(proj.uuid) in uuids

    def test_private_project_excluded_from_list_without_perm(self):
        """User without view_project perm does NOT see private project in list."""
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # no perm
        response = client.get(reverse("project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(proj.uuid) not in uuids


# ---------------------------------------------------------------------------
# Dataset permission tests (same pattern, verifying it generalises)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetPermissions:
    """Permission enforcement for Dataset endpoints."""

    def test_anonymous_cannot_see_private_dataset_detail(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        url = reverse("dataset-detail", kwargs={"uuid": ds.uuid})
        assert APIClient().get(url).status_code == 404

    def test_permitted_user_can_see_private_dataset(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        user = UserFactory()
        assign_perm("view_dataset", user, ds)
        client = make_token_client(user)
        url = reverse("dataset-detail", kwargs={"uuid": ds.uuid})
        assert client.get(url).status_code == 200
