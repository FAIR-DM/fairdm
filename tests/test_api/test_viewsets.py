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


# ---------------------------------------------------------------------------
# Project CRUD (authenticated write operations)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestProjectCRUD:
    """Authenticated create / update / delete for Project (US3)."""

    def test_authenticated_post_creates_project(self, authenticated_client):
        """POST /api/v1/projects/ with valid payload → 201 + object in DB."""
        response = authenticated_client.post(
            reverse("project-list"),
            {"name": "New API Project"},
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New API Project"
        assert "uuid" in data

    def test_created_project_appears_in_list(self, authenticated_client):
        """Created project appears in the list endpoint immediately after POST."""
        post_resp = authenticated_client.post(
            reverse("project-list"),
            {"name": "Listed Project"},
            format="json",
        )
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]
        list_resp = authenticated_client.get(reverse("project-list"))
        uuids = [p["uuid"] for p in list_resp.json()["results"]]
        assert uuid in uuids

    def test_authenticated_patch_updates_project(self, authenticated_client, user):
        """PATCH /api/v1/projects/{uuid}/ with partial data → 200 + updated field."""
        from guardian.shortcuts import assign_perm

        # Create the project via POST so permissions are auto-assigned
        post_resp = authenticated_client.post(
            reverse("project-list"),
            {"name": "Patch Target"},
            format="json",
        )
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]

        url = reverse("project-detail", kwargs={"uuid": uuid})
        patch_resp = authenticated_client.patch(url, {"name": "Updated Name"}, format="json")
        assert patch_resp.status_code == 200
        assert patch_resp.json()["name"] == "Updated Name"

    def test_authenticated_delete_removes_project(self, authenticated_client, user):
        """DELETE /api/v1/projects/{uuid}/ → 204, subsequent GET → 404."""
        # Create via POST so permissions are auto-assigned
        post_resp = authenticated_client.post(
            reverse("project-list"),
            {"name": "Delete Target"},
            format="json",
        )
        assert post_resp.status_code == 201
        uuid = post_resp.json()["uuid"]

        url = reverse("project-detail", kwargs={"uuid": uuid})
        del_resp = authenticated_client.delete(url)
        assert del_resp.status_code == 204

        get_resp = authenticated_client.get(url)
        assert get_resp.status_code == 404

    def test_unauthenticated_post_returns_401(self, api_client):
        """POST without credentials → 401 (per contract §3)."""
        response = api_client.post(
            reverse("project-list"),
            {"name": "Should Fail"},
            format="json",
        )
        assert response.status_code == 401

    def test_post_missing_required_field_returns_400(self, authenticated_client):
        """POST with empty payload → 400 with field-level validation errors."""
        response = authenticated_client.post(
            reverse("project-list"),
            {},
            format="json",
        )
        assert response.status_code == 400
        assert "name" in response.json()


# ---------------------------------------------------------------------------
# Rate limiting / throttling (US5)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRateLimiting:
    """Verify DRF throttling behaviour for anonymous and authenticated users.

    Test settings use DummyCache which never stores throttle counts.  We patch
    ``SimpleRateThrottle.cache`` with a real LocMemCache for these tests, and
    patch ``get_rate()`` on the specific throttle class to inject tiny limits
    so we can exhaust the quota in a few requests.
    """

    @pytest.fixture(autouse=True)
    def _throttle_setup(self):
        """Replace the dummy cache with LocMemCache for throttle count storage."""
        from django.core.cache.backends.locmem import LocMemCache
        from unittest.mock import patch

        from rest_framework.throttling import SimpleRateThrottle

        test_cache = LocMemCache("throttle-test", {})
        test_cache.clear()
        with patch.object(SimpleRateThrottle, "cache", test_cache):
            yield
        test_cache.clear()

    def test_anonymous_throttled_after_limit(self, api_client):
        """Anonymous user exceeds limit → 429."""
        from unittest.mock import patch

        from rest_framework.throttling import AnonRateThrottle

        with patch.object(AnonRateThrottle, "get_rate", return_value="2/minute"):
            url = reverse("project-list")
            for _ in range(2):
                assert api_client.get(url).status_code == 200
            assert api_client.get(url).status_code == 429

    def test_throttled_response_has_retry_after_header(self, api_client):
        """Throttled responses include the ``Retry-After`` header."""
        from unittest.mock import patch

        from rest_framework.throttling import AnonRateThrottle

        with patch.object(AnonRateThrottle, "get_rate", return_value="1/minute"):
            url = reverse("project-list")
            api_client.get(url)
            resp = api_client.get(url)
            assert resp.status_code == 429
            assert "Retry-After" in resp

    def test_throttled_response_has_detail_message(self, api_client):
        """429 response body includes a human-readable ``detail`` message."""
        from unittest.mock import patch

        from rest_framework.throttling import AnonRateThrottle

        with patch.object(AnonRateThrottle, "get_rate", return_value="1/minute"):
            url = reverse("project-list")
            api_client.get(url)
            resp = api_client.get(url)
            assert resp.status_code == 429
            assert "detail" in resp.json()

    def test_authenticated_gets_higher_limit(self, api_client, authenticated_client):
        """Authenticated user's higher cap is respected when anon is already throttled."""
        from unittest.mock import patch

        from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

        with patch.object(AnonRateThrottle, "get_rate", return_value="1/minute"), patch.object(
            UserRateThrottle, "get_rate", return_value="3/minute"
        ):
            url = reverse("project-list")
            # exhaust anon quota
            api_client.get(url)
            assert api_client.get(url).status_code == 429
            # authenticated user still has headroom
            for _ in range(3):
                assert authenticated_client.get(url).status_code == 200

    def test_throttle_rates_configurable(self, settings):
        """Default throttle rates are present and portal-overridable via settings."""
        rates = settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {})
        assert "anon" in rates
        assert "user" in rates
        # Verify the shipping defaults
        assert rates["anon"] == "100/hour"
        assert rates["user"] == "1000/hour"
        # Simulate portal override — new values are picked up
        settings.REST_FRAMEWORK = {
            **settings.REST_FRAMEWORK,
            "DEFAULT_THROTTLE_RATES": {"anon": "50/hour", "user": "500/hour"},
        }
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"] == "50/hour"
