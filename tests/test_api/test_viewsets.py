"""Tests for FairDM API viewsets (Feature 011 — US1).

Covers:
- List and detail endpoints for Project, Dataset, Contributor
- Visibility filtering: public vs private access (anonymous + authenticated)
- Ordering filter: ?ordering=field and ?ordering=-field
- CRUD write-protection (unauthenticated writes return 401)
"""

import pytest
from django.urls import reverse

from fairdm.factories import DatasetFactory, ProjectFactory
from fairdm.utils.choices import Visibility


# ---------------------------------------------------------------------------
# Project list
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectListEndpoint:
    """GET /api/v1/projects/"""

    def test_returns_200(self, api_client):
        response = api_client.get(reverse("project-list"))
        assert response.status_code == 200

    def test_response_has_pagination_keys(self, api_client):
        response = api_client.get(reverse("project-list"))
        data = response.json()
        for key in ("count", "next", "previous", "results"):
            assert key in data

    def test_public_project_visible_to_anonymous(self, api_client, public_project):
        response = api_client.get(reverse("project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(public_project.uuid) in uuids

    def test_private_project_hidden_from_anonymous(self, api_client, private_project):
        response = api_client.get(reverse("project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(private_project.uuid) not in uuids

    def test_authenticated_sees_public_project(self, authenticated_client, public_project):
        response = authenticated_client.get(reverse("project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(public_project.uuid) in uuids

    def test_authenticated_still_hidden_from_private_without_permission(
        self, authenticated_client, private_project
    ):
        response = authenticated_client.get(reverse("project-list"))
        uuids = [p["uuid"] for p in response.json()["results"]]
        assert str(private_project.uuid) not in uuids

    def test_ordering_ascending(self, api_client, db):
        """?ordering=name returns names in A→Z order."""
        ProjectFactory(name="Zeta Project", visibility=Visibility.PUBLIC)
        ProjectFactory(name="Alpha Project", visibility=Visibility.PUBLIC)
        response = api_client.get(reverse("project-list"), {"ordering": "name"})
        assert response.status_code == 200
        names = [p["name"] for p in response.json()["results"]]
        assert names == sorted(names)

    def test_ordering_descending(self, api_client, db):
        """?ordering=-name returns names in Z→A order."""
        ProjectFactory(name="Zeta Project", visibility=Visibility.PUBLIC)
        ProjectFactory(name="Alpha Project", visibility=Visibility.PUBLIC)
        response = api_client.get(reverse("project-list"), {"ordering": "-name"})
        assert response.status_code == 200
        names = [p["name"] for p in response.json()["results"]]
        assert names == sorted(names, reverse=True)

    def test_unauthenticated_post_returns_401(self, api_client):
        response = api_client.post(reverse("project-list"), {"name": "New Project"}, format="json")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Project detail
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectDetailEndpoint:
    """GET /api/v1/projects/{uuid}/"""

    def test_public_project_returns_200(self, api_client, public_project):
        url = reverse("project-detail", kwargs={"uuid": public_project.uuid})
        response = api_client.get(url)
        assert response.status_code == 200

    def test_public_project_uuid_in_response(self, api_client, public_project):
        url = reverse("project-detail", kwargs={"uuid": public_project.uuid})
        response = api_client.get(url)
        assert response.json()["uuid"] == str(public_project.uuid)

    def test_public_project_has_expected_fields(self, api_client, public_project):
        url = reverse("project-detail", kwargs={"uuid": public_project.uuid})
        response = api_client.get(url)
        data = response.json()
        for field in ("uuid", "name", "visibility"):
            assert field in data

    def test_private_project_returns_404_to_anonymous(self, api_client, private_project):
        url = reverse("project-detail", kwargs={"uuid": private_project.uuid})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_nonexistent_uuid_returns_404(self, api_client):
        url = reverse("project-detail", kwargs={"uuid": "nonexistentid"})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_unauthenticated_patch_returns_401(self, api_client, public_project):
        url = reverse("project-detail", kwargs={"uuid": public_project.uuid})
        response = api_client.patch(url, {"name": "Hacked"}, format="json")
        assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Dataset list
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetListEndpoint:
    """GET /api/v1/datasets/"""

    def test_returns_200(self, api_client):
        response = api_client.get(reverse("dataset-list"))
        assert response.status_code == 200

    def test_public_dataset_visible_to_anonymous(self, api_client, public_dataset):
        response = api_client.get(reverse("dataset-list"))
        uuids = [d["uuid"] for d in response.json()["results"]]
        assert str(public_dataset.uuid) in uuids

    def test_private_dataset_hidden_from_anonymous(self, api_client, private_dataset):
        response = api_client.get(reverse("dataset-list"))
        uuids = [d["uuid"] for d in response.json()["results"]]
        assert str(private_dataset.uuid) not in uuids

    def test_response_has_expected_fields(self, api_client, public_dataset):
        response = api_client.get(reverse("dataset-list"))
        results = response.json()["results"]
        ds = next((d for d in results if d["uuid"] == str(public_dataset.uuid)), None)
        assert ds is not None
        for field in ("uuid", "name", "visibility"):
            assert field in ds

    def test_dataset_ordering_ascending(self, api_client, public_project, db):
        DatasetFactory(project=public_project, name="A Dataset", visibility=Visibility.PUBLIC)
        DatasetFactory(project=public_project, name="Z Dataset", visibility=Visibility.PUBLIC)
        response = api_client.get(reverse("dataset-list"), {"ordering": "name"})
        assert response.status_code == 200
        names = [d["name"] for d in response.json()["results"]]
        assert names == sorted(names)


# ---------------------------------------------------------------------------
# Dataset detail
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetDetailEndpoint:
    """GET /api/v1/datasets/{uuid}/"""

    def test_public_dataset_returns_200(self, api_client, public_dataset):
        url = reverse("dataset-detail", kwargs={"uuid": public_dataset.uuid})
        response = api_client.get(url)
        assert response.status_code == 200

    def test_private_dataset_returns_404_to_anonymous(self, api_client, private_dataset):
        url = reverse("dataset-detail", kwargs={"uuid": private_dataset.uuid})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_nonexistent_uuid_returns_404(self, api_client):
        url = reverse("dataset-detail", kwargs={"uuid": "doesnotexist"})
        response = api_client.get(url)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Contributor list
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestContributorListEndpoint:
    """GET /api/v1/contributors/ — read-only, all contributors publicly accessible."""

    def test_returns_200(self, api_client):
        response = api_client.get(reverse("contributor-list"))
        assert response.status_code == 200

    def test_has_pagination_keys(self, api_client):
        data = api_client.get(reverse("contributor-list")).json()
        for key in ("count", "next", "previous", "results"):
            assert key in data

    def test_post_not_allowed(self, authenticated_client):
        """ContributorViewSet is read-only; POST must be rejected (405 or 403)."""
        response = authenticated_client.post(
            reverse("contributor-list"), {"name": "New"}, format="json"
        )
        # DRF may return 403 (permission denied) before 405 (method not allowed)
        # when object-level permissions fire before method routing.
        assert response.status_code in (403, 405)
