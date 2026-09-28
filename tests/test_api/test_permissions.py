"""Permission enforcement tests for FairDM API (Feature 011 â€” US4)."""

import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


def make_token_client(user) -> APIClient:
    """Return an APIClient authenticated as *user* via token."""
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.mark.django_db
class TestAnonymousAccess:
    def test_list_returns_200(self):
        response = APIClient().get(reverse("api:project-list"))
        assert response.status_code == 200

    def test_public_project_detail_returns_200(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().get(url).status_code == 200

    def test_private_project_detail_returns_404(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().get(url).status_code == 404

    def test_post_returns_401(self):
        response = APIClient().post(
            reverse("api:project-list"), {"name": "X"}, format="json"
        )
        assert response.status_code == 401

    def test_patch_public_project_returns_401(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        response = APIClient().patch(url, {"name": "Hacked"}, format="json")
        assert response.status_code == 401

    def test_delete_public_project_returns_401(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert APIClient().delete(url).status_code == 401


@pytest.mark.django_db
class TestAuthenticatedNoPermission:
    def test_private_project_detail_returns_404(self):
        owner = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # different user, no perms
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert client.get(url).status_code == 404

    def test_patch_public_project_returns_403(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        client = make_token_client(UserFactory())  # no guardian perm
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        response = client.patch(url, {"name": "Hijack"}, format="json")
        assert response.status_code == 403

    def test_patch_private_project_returns_404(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # no guardian perm
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        response = client.patch(url, {"name": "Hijack"}, format="json")
        assert response.status_code == 404

    def test_delete_private_project_returns_404(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert client.delete(url).status_code == 404

    def test_create_project_succeeds(self):
        client = make_token_client(UserFactory())
        response = client.post(
            reverse("api:project-list"), {"name": "My New Project"}, format="json"
        )
        assert response.status_code == 201


@pytest.mark.django_db
class TestAuthenticatedWithPermission:
    def test_view_perm_allows_private_project_read(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        client = make_token_client(user)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert client.get(url).status_code == 200

    def test_change_perm_allows_patch(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        assign_perm("change_project", user, proj)
        client = make_token_client(user)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        resp = client.patch(url, {"name": "Updated"}, format="json")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_delete_perm_allows_delete(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        assign_perm("delete_project", user, proj)
        client = make_token_client(user)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        assert client.delete(url).status_code == 204

    def test_owner_created_object_gets_full_access(self):
        user = UserFactory()
        client = make_token_client(user)

        post_resp = client.post(
            reverse("api:project-list"), {"name": "Owner Project"}, format="json"
        )
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]
        url = reverse("api:project-detail", kwargs={"uuid": uuid})

        patch_resp = client.patch(url, {"name": "Renamed"}, format="json")
        assert patch_resp.status_code == 200

        del_resp = client.delete(url)
        assert del_resp.status_code == 204

    def test_viewer_cannot_patch_private_project(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)  # view but not change
        client = make_token_client(user)
        url = reverse("api:project-detail", kwargs={"uuid": proj.uuid})
        resp = client.patch(url, {"name": "No Access"}, format="json")
        assert resp.status_code == 403

    def test_private_project_appears_in_list_for_permitted_user(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        client = make_token_client(user)
        response = client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(proj.uuid) in uuids

    def test_private_project_excluded_from_list_without_perm(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        client = make_token_client(UserFactory())  # no perm
        response = client.get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(proj.uuid) not in uuids


@pytest.mark.django_db
class TestDatasetPermissions:
    def test_anonymous_cannot_see_private_dataset_detail(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        url = reverse("api:dataset-detail", kwargs={"uuid": ds.uuid})
        assert APIClient().get(url).status_code == 404

    def test_permitted_user_can_see_private_dataset(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        user = UserFactory()
        assign_perm("view_dataset", user, ds)
        client = make_token_client(user)
        url = reverse("api:dataset-detail", kwargs={"uuid": ds.uuid})
        assert client.get(url).status_code == 200
