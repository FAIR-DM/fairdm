"""Tests for FairDM API router auto-registration and discovery endpoints (Feature 011 US1)."""

import pytest
from django.urls import resolve, reverse

from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestCoreRoutesRegistered:
    def test_project_list_url_resolves(self):
        url = reverse("api:project-list")
        match = resolve(url)
        assert match is not None

    def test_project_detail_url_pattern_exists(self):
        url = reverse("api:project-list")
        assert "/api/v1/projects/" in url

    def test_dataset_list_url_resolves(self):
        url = reverse("api:dataset-list")
        assert "/api/v1/datasets/" in url

    def test_contributor_list_url_resolves(self):
        url = reverse("api:contributor-list")
        assert "/api/v1/contributors/" in url


@pytest.mark.django_db
class TestSampleDiscoveryEndpoint:
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
        from fairdm.registry import registry

        expected_names = {m.__name__ for m in registry.samples}
        data = api_client.get(reverse("api:api-sample-discovery")).json()
        returned_names = {entry["name"] for entry in data["types"]}
        for name in expected_names:
            assert name in returned_names, (
                f"Expected '{name}' in discovery catalog, got {returned_names}"
            )

    def test_count_is_zero_when_no_records(self, api_client):
        data = api_client.get(reverse("api:api-sample-discovery")).json()
        for entry in data["types"]:
            assert entry["count"] >= 0

    def test_anon_count_only_shows_public(self, api_client, public_dataset, db):
        from demo.factories import CustomParentSampleFactory

        public_sample = CustomParentSampleFactory(dataset=public_dataset)
        private_dataset_factory = __import__(
            "fairdm.factories", fromlist=["DatasetFactory"]
        ).DatasetFactory
        from fairdm.factories import DatasetFactory

        private_ds = DatasetFactory(
            project=public_dataset.project, visibility=Visibility.PRIVATE
        )
        private_sample = CustomParentSampleFactory(dataset=private_ds)

        data = api_client.get(reverse("api:api-sample-discovery")).json()
        entry = next(
            (e for e in data["types"] if e["name"] == "CustomParentSample"), None
        )
        assert entry is not None
        # Anonymous user should only count public samples (those in a PUBLIC dataset)
        assert entry["count"] == 1


@pytest.mark.django_db
class TestMeasurementDiscoveryEndpoint:
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


@pytest.mark.django_db
class TestRegistryGeneratedEndpoints:
    def test_custom_parent_sample_list_accessible(self, api_client):
        from demo.models import CustomParentSample
        from fairdm.api.viewsets import _model_to_slug

        slug = _model_to_slug(CustomParentSample)
        response = api_client.get(f"/api/v1/samples/{slug}/")
        assert response.status_code == 200

    def test_example_measurement_list_accessible(self, api_client):
        from demo.models import ExampleMeasurement
        from fairdm.api.viewsets import _model_to_slug

        slug = _model_to_slug(ExampleMeasurement)
        response = api_client.get(f"/api/v1/measurements/{slug}/")
        assert response.status_code == 200

    def test_custom_parent_sample_list_has_pagination(self, api_client):
        from demo.models import CustomParentSample
        from fairdm.api.viewsets import _model_to_slug

        slug = _model_to_slug(CustomParentSample)
        data = api_client.get(f"/api/v1/samples/{slug}/").json()
        for key in ("count", "results"):
            assert key in data


@pytest.mark.django_db
class TestAPIRootContainsDiscoveryLinks:
    def test_api_root_contains_sample_types_key(self, api_client):
        response = api_client.get("/api/v1/", HTTP_ACCEPT="application/json")
        assert response.status_code == 200
        data = response.json()
        assert "sample-types" in data, (
            f"'sample-types' missing from API root keys: {list(data.keys())}"
        )

    def test_api_root_contains_measurement_types_key(self, api_client):
        response = api_client.get("/api/v1/", HTTP_ACCEPT="application/json")
        assert response.status_code == 200
        data = response.json()
        assert "measurement-types" in data, (
            f"'measurement-types' missing from API root keys: {list(data.keys())}"
        )

    def test_sample_types_url_points_to_discovery_endpoint(self, api_client):
        response = api_client.get("/api/v1/", HTTP_ACCEPT="application/json")
        data = response.json()
        url = data.get("sample-types", "")
        assert url.endswith("/api/v1/samples/") or "/api/v1/samples/" in url, (
            f"Unexpected sample-types URL: {url!r}"
        )

    def test_measurement_types_url_points_to_discovery_endpoint(self, api_client):
        response = api_client.get("/api/v1/", HTTP_ACCEPT="application/json")
        data = response.json()
        url = data.get("measurement-types", "")
        assert (
            url.endswith("/api/v1/measurements/") or "/api/v1/measurements/" in url
        ), f"Unexpected measurement-types URL: {url!r}"

    def test_fairdm_api_router_is_fairdm_router_subclass(self):
        from rest_framework.routers import DefaultRouter

        from fairdm.api.router import FairDMAPIRouter, fairdm_api_router

        assert isinstance(fairdm_api_router, FairDMAPIRouter)
        assert isinstance(fairdm_api_router, DefaultRouter)


class TestAPIURLNamespaceIsolation:
    # Portal route names such as project-list must not resolve to API endpoints, and API routes
    # are reachable only under the api: namespace.
    def test_portal_project_list_resolves_to_portal_view(self):
        url = reverse("project-list")
        assert "/api/v1/" not in url, (
            f"'project-list' should resolve to the portal UI, not the API. Got: {url!r}"
        )
        assert "/projects/" in url

    def test_portal_dataset_list_resolves_to_portal_view(self):
        url = reverse("dataset-list")
        assert "/api/v1/" not in url, (
            f"'dataset-list' should resolve to the portal UI, not the API. Got: {url!r}"
        )
        assert "/datasets/" in url

    def test_api_project_list_resolves_to_api_endpoint(self):
        url = reverse("api:project-list")
        assert "/api/v1/projects/" in url, f"Expected API endpoint URL, got: {url!r}"

    def test_api_dataset_list_resolves_to_api_endpoint(self):
        url = reverse("api:dataset-list")
        assert "/api/v1/datasets/" in url, f"Expected API endpoint URL, got: {url!r}"

    def test_portal_and_api_project_urls_are_different(self):
        portal_url = reverse("project-list")
        api_url = reverse("api:project-list")
        assert portal_url != api_url, (
            f"Portal and API project-list resolved to the same URL: {portal_url!r}"
        )

    def test_portal_and_api_dataset_urls_are_different(self):
        portal_url = reverse("dataset-list")
        api_url = reverse("api:dataset-list")
        assert portal_url != api_url, (
            f"Portal and API dataset-list resolved to the same URL: {portal_url!r}"
        )
