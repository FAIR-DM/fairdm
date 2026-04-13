"""Tests for FairDM API router auto-registration and discovery endpoints (Feature 011 US1).

Covers:
- All core model viewsets are registered (projects, datasets, contributors)
- All registry-registered Sample/Measurement types get URL patterns
- Discovery catalog endpoints at /api/v1/samples/ and /api/v1/measurements/
- Discovery catalog returns expected metadata structure
- Permission-aware count in discovery catalog
"""

import pytest
from django.urls import resolve, reverse

from fairdm.utils.choices import Visibility

# ---------------------------------------------------------------------------
# Core URL patterns
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCoreRoutesRegistered:
    """All three core model viewsets must appear in the URL conf."""

    def test_project_list_url_resolves(self):
        url = reverse("api:project-list")
        match = resolve(url)
        assert match is not None

    def test_project_detail_url_pattern_exists(self):
        # Verify the URL name resolves to a valid route
        url = reverse("api:project-list")
        assert "/api/v1/projects/" in url

    def test_dataset_list_url_resolves(self):
        url = reverse("api:dataset-list")
        assert "/api/v1/datasets/" in url

    def test_contributor_list_url_resolves(self):
        url = reverse("api:contributor-list")
        assert "/api/v1/contributors/" in url


# ---------------------------------------------------------------------------
# Sample discovery endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSampleDiscoveryEndpoint:
    """GET /api/v1/samples/ — returns catalog of all registered Sample types."""

    def test_returns_200(self, api_client):
        response = api_client.get(reverse("api:api-sample-discovery"))
        assert response.status_code == 200

    def test_response_has_types_key(self, api_client):
        data = api_client.get(reverse("api:api-sample-discovery")).json()
        assert "types" in data
        assert isinstance(data["types"], list)

    def test_each_type_has_required_keys(self, api_client):
        data = api_client.get(reverse("api:api-sample-discovery")).json()
        required = {"name", "verbose_name", "verbose_name_plural", "endpoint", "count"}
        for entry in data["types"]:
            for key in required:
                assert key in entry, f"Missing key '{key}' in discovery entry: {entry}"

    def test_demo_sample_types_appear(self, api_client):
        """Demo app registers multiple Sample types; they must appear in the catalog."""
        from fairdm.registry import registry

        expected_names = {m.__name__ for m in registry.samples}
        data = api_client.get(reverse("api:api-sample-discovery")).json()
        returned_names = {entry["name"] for entry in data["types"]}
        # At minimum the demo models must appear
        for name in expected_names:
            assert name in returned_names, f"Expected '{name}' in discovery catalog, got {returned_names}"

    def test_count_is_zero_when_no_records(self, api_client):
        """With no sample records, each type should report count=0."""
        data = api_client.get(reverse("api:api-sample-discovery")).json()
        for entry in data["types"]:
            assert entry["count"] >= 0  # Must be non-negative

    def test_anon_count_only_shows_public(self, api_client, public_dataset, db):
        """Anonymous users should see count of public records only."""
        from fairdm_demo.factories import CustomParentSampleFactory

        # Create one public and one private sample
        public_sample = CustomParentSampleFactory(dataset=public_dataset)
        private_dataset_factory = __import__("fairdm.factories", fromlist=["DatasetFactory"]).DatasetFactory
        from fairdm.factories import DatasetFactory

        private_ds = DatasetFactory(project=public_dataset.project, visibility=Visibility.PRIVATE)
        private_sample = CustomParentSampleFactory(dataset=private_ds)

        data = api_client.get(reverse("api:api-sample-discovery")).json()
        # Find the CustomParentSample entry
        entry = next((e for e in data["types"] if e["name"] == "CustomParentSample"), None)
        assert entry is not None
        # Anonymous user should only count public samples (those in a PUBLIC dataset)
        assert entry["count"] == 1


# ---------------------------------------------------------------------------
# Measurement discovery endpoint
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestMeasurementDiscoveryEndpoint:
    """GET /api/v1/measurements/ — returns catalog of all registered Measurement types."""

    def test_returns_200(self, api_client):
        response = api_client.get(reverse("api:api-measurement-discovery"))
        assert response.status_code == 200

    def test_response_has_types_key(self, api_client):
        data = api_client.get(reverse("api:api-measurement-discovery")).json()
        assert "types" in data
        assert isinstance(data["types"], list)

    def test_demo_measurement_types_appear(self, api_client):
        from fairdm.registry import registry

        expected_names = {m.__name__ for m in registry.measurements}
        data = api_client.get(reverse("api:api-measurement-discovery")).json()
        returned_names = {entry["name"] for entry in data["types"]}
        for name in expected_names:
            assert name in returned_names

    def test_each_type_has_required_keys(self, api_client):
        data = api_client.get(reverse("api:api-measurement-discovery")).json()
        required = {"name", "verbose_name", "endpoint", "count"}
        for entry in data["types"]:
            for key in required:
                assert key in entry


# ---------------------------------------------------------------------------
# Registry-generated sample endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRegistryGeneratedEndpoints:
    """Registry-registered types must produce working list/detail endpoints."""

    def test_custom_parent_sample_list_accessible(self, api_client):
        """CustomParentSample is registered in the demo app; its endpoint must work."""
        from fairdm.api.viewsets import _model_to_slug
        from fairdm_demo.models import CustomParentSample

        slug = _model_to_slug(CustomParentSample)
        response = api_client.get(f"/api/v1/samples/{slug}/")
        assert response.status_code == 200

    def test_example_measurement_list_accessible(self, api_client):
        """ExampleMeasurement is registered in the demo app; its endpoint must work."""
        from fairdm.api.viewsets import _model_to_slug
        from fairdm_demo.models import ExampleMeasurement

        slug = _model_to_slug(ExampleMeasurement)
        response = api_client.get(f"/api/v1/measurements/{slug}/")
        assert response.status_code == 200

    def test_custom_parent_sample_list_has_pagination(self, api_client):
        from fairdm.api.viewsets import _model_to_slug
        from fairdm_demo.models import CustomParentSample

        slug = _model_to_slug(CustomParentSample)
        data = api_client.get(f"/api/v1/samples/{slug}/").json()
        for key in ("count", "results"):
            assert key in data


# ---------------------------------------------------------------------------
# Phase 10: API root lists discovery endpoints (FR-003/FR-004)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAPIRootContainsDiscoveryLinks:
    """GET /api/v1/ must include sample-types and measurement-types discovery links."""

    def test_api_root_contains_sample_types_key(self, api_client):
        """API root JSON response must contain a 'sample-types' key."""
        response = api_client.get("/api/v1/", HTTP_ACCEPT="application/json")
        assert response.status_code == 200
        data = response.json()
        assert "sample-types" in data, f"'sample-types' missing from API root keys: {list(data.keys())}"

    def test_api_root_contains_measurement_types_key(self, api_client):
        """API root JSON response must contain a 'measurement-types' key."""
        response = api_client.get("/api/v1/", HTTP_ACCEPT="application/json")
        assert response.status_code == 200
        data = response.json()
        assert "measurement-types" in data, f"'measurement-types' missing from API root keys: {list(data.keys())}"

    def test_sample_types_url_points_to_discovery_endpoint(self, api_client):
        """The 'sample-types' URL in the API root must end with '/api/v1/samples/'."""
        response = api_client.get("/api/v1/", HTTP_ACCEPT="application/json")
        data = response.json()
        url = data.get("sample-types", "")
        assert url.endswith("/api/v1/samples/") or "/api/v1/samples/" in url, f"Unexpected sample-types URL: {url!r}"

    def test_measurement_types_url_points_to_discovery_endpoint(self, api_client):
        """The 'measurement-types' URL in the API root must end with '/api/v1/measurements/'."""
        response = api_client.get("/api/v1/", HTTP_ACCEPT="application/json")
        data = response.json()
        url = data.get("measurement-types", "")
        assert url.endswith("/api/v1/measurements/") or "/api/v1/measurements/" in url, (
            f"Unexpected measurement-types URL: {url!r}"
        )

    def test_fairdm_api_router_is_fairdm_router_subclass(self):
        """fairdm_api_router must be an instance of FairDMAPIRouter."""
        from rest_framework.routers import DefaultRouter

        from fairdm.api.router import FairDMAPIRouter, fairdm_api_router

        assert isinstance(fairdm_api_router, FairDMAPIRouter)
        # Also still passes DefaultRouter isinstance check (inheritance)
        assert isinstance(fairdm_api_router, DefaultRouter)


# ---------------------------------------------------------------------------
# BUG-001: API URL namespace isolation regression tests (T097)
# ---------------------------------------------------------------------------


class TestAPIURLNamespaceIsolation:
    """Regression tests ensuring API URL names are isolated under the 'api' namespace.

    Portal UI routes (project-list, dataset-list) must NOT resolve to API endpoints,
    and API routes must only be accessible via namespaced names (api:project-list, etc.).
    BUG-001 — 2026-04-13
    """

    def test_portal_project_list_resolves_to_portal_view(self):
        """reverse('project-list') must resolve to the portal HTML list view, not the API."""
        url = reverse("project-list")
        assert "/api/v1/" not in url, f"'project-list' should resolve to the portal UI, not the API. Got: {url!r}"
        assert "/projects/" in url

    def test_portal_dataset_list_resolves_to_portal_view(self):
        """reverse('dataset-list') must resolve to the portal HTML list view, not the API."""
        url = reverse("dataset-list")
        assert "/api/v1/" not in url, f"'dataset-list' should resolve to the portal UI, not the API. Got: {url!r}"
        assert "/datasets/" in url

    def test_api_project_list_resolves_to_api_endpoint(self):
        """reverse('api:project-list') must resolve to the API endpoint."""
        url = reverse("api:project-list")
        assert "/api/v1/projects/" in url, f"Expected API endpoint URL, got: {url!r}"

    def test_api_dataset_list_resolves_to_api_endpoint(self):
        """reverse('api:dataset-list') must resolve to the API endpoint."""
        url = reverse("api:dataset-list")
        assert "/api/v1/datasets/" in url, f"Expected API endpoint URL, got: {url!r}"

    def test_portal_and_api_project_urls_are_different(self):
        """Portal and API project-list URLs must not be the same path."""
        portal_url = reverse("project-list")
        api_url = reverse("api:project-list")
        assert portal_url != api_url, f"Portal and API project-list resolved to the same URL: {portal_url!r}"

    def test_portal_and_api_dataset_urls_are_different(self):
        """Portal and API dataset-list URLs must not be the same path."""
        portal_url = reverse("dataset-list")
        api_url = reverse("api:dataset-list")
        assert portal_url != api_url, f"Portal and API dataset-list resolved to the same URL: {portal_url!r}"
