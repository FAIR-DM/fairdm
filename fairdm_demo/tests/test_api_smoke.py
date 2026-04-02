"""
FairDM Demo App — API Smoke Tests (Feature 011 T048)

Verifies that demo app Sample and Measurement models registered via the FairDM
registry get correctly auto-generated API endpoints, appear in the discovery
catalogs, and return sensible data from list/detail endpoints.

These tests serve as a live sanity check that the framework's API generation
pipeline works end-to-end with real models defined by a portal developer.
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from fairdm.utils.choices import Visibility

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture()
def api_client():
    return APIClient()


# ---------------------------------------------------------------------------
# Discovery catalog smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDemoSampleDiscovery:
    """Demo Sample types appear correctly in the discovery catalog."""

    def test_sample_discovery_returns_200(self, api_client):
        resp = api_client.get(reverse("api-sample-discovery"))
        assert resp.status_code == 200

    def test_demo_samples_in_catalog(self, api_client):
        """All registered demo sample types appear in the discovery catalog."""
        from fairdm.registry import registry

        resp = api_client.get(reverse("api-sample-discovery"))
        data = resp.json()
        types = data.get("types", [])
        catalog_names = {t["name"] for t in types}

        for model in registry.samples:
            assert model.__name__ in catalog_names, f"Expected demo Sample '{model.__name__}' in discovery catalog"

    def test_catalog_entries_have_required_keys(self, api_client):
        """Each catalog entry has name, endpoint, fields, and count keys."""
        resp = api_client.get(reverse("api-sample-discovery"))
        for entry in resp.json().get("types", []):
            for key in ("name", "endpoint", "fields", "count"):
                assert key in entry, f"Missing key '{key}' in catalog entry: {entry}"


@pytest.mark.django_db
class TestDemoMeasurementDiscovery:
    """Demo Measurement types appear correctly in the discovery catalog."""

    def test_measurement_discovery_returns_200(self, api_client):
        resp = api_client.get(reverse("api-measurement-discovery"))
        assert resp.status_code == 200

    def test_demo_measurements_in_catalog(self, api_client):
        """All registered demo measurement types appear in the discovery catalog."""
        from fairdm.registry import registry

        resp = api_client.get(reverse("api-measurement-discovery"))
        data = resp.json()
        types = data.get("types", [])
        catalog_names = {t["name"] for t in types}

        for model in registry.measurements:
            assert model.__name__ in catalog_names, f"Expected demo Measurement '{model.__name__}' in discovery catalog"


# ---------------------------------------------------------------------------
# List endpoint smoke tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDemoSampleListEndpoints:
    """Auto-generated list endpoints for demo Sample types return valid responses."""

    def test_custom_parent_sample_list_returns_200(self, api_client):
        resp = api_client.get(reverse("samples-custom-parent-sample-list"))
        assert resp.status_code == 200

    def test_custom_parent_sample_list_has_pagination_keys(self, api_client):
        resp = api_client.get(reverse("samples-custom-parent-sample-list"))
        data = resp.json()
        for key in ("count", "next", "previous", "results"):
            assert key in data

    def test_public_sample_visible_to_anonymous(self, api_client, db):
        """A public sample appears in the list for anonymous users."""
        from fairdm.factories import DatasetFactory, ProjectFactory
        from fairdm_demo.factories import CustomParentSampleFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        sample = CustomParentSampleFactory(dataset=dataset)

        resp = api_client.get(reverse("samples-custom-parent-sample-list"))
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert len(results) >= 1  # At least our sample appears

    def test_sample_count_in_discovery_reflects_public_records(self, api_client, db):
        """Discovery catalog count for anonymous user matches public-only records."""
        from fairdm.factories import DatasetFactory, ProjectFactory
        from fairdm_demo.factories import CustomParentSampleFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        CustomParentSampleFactory.create_batch(3, dataset=dataset)

        resp = api_client.get(reverse("api-sample-discovery"))
        types = resp.json().get("types", [])
        entry = next((t for t in types if t["name"] == "CustomParentSample"), None)
        assert entry is not None
        assert entry["count"] == 3


@pytest.mark.django_db
class TestDemoMeasurementListEndpoints:
    """Auto-generated list endpoint for ExampleMeasurement returns valid response."""

    def test_example_measurement_list_returns_200(self, api_client):
        resp = api_client.get(reverse("measurements-example-measurement-list"))
        assert resp.status_code == 200

    def test_example_measurement_list_has_pagination_keys(self, api_client):
        data = api_client.get(reverse("measurements-example-measurement-list")).json()
        for key in ("count", "next", "previous", "results"):
            assert key in data
