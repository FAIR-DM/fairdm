"""FairDM Demo App — API Smoke Tests (Feature 011 T048)."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from fairdm.utils.choices import Visibility


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestDemoSampleListEndpoints:
    def test_custom_parent_sample_list_returns_200(self, api_client):
        resp = api_client.get(reverse("api:samples-custom-parent-samples-list"))
        assert resp.status_code == 200

    def test_public_sample_visible_to_anonymous(self, api_client, db):
        from demo.factories import CustomParentSampleFactory
        from fairdm.factories import DatasetFactory, ProjectFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        sample = CustomParentSampleFactory(dataset=dataset)

        resp = api_client.get(reverse("api:samples-custom-parent-samples-list"))
        assert resp.status_code == 200
        assert sample.uuid in [row["uuid"] for row in resp.json()["results"]]


@pytest.mark.django_db
class TestDemoMeasurementListEndpoints:
    def test_example_measurement_list_returns_200(self, api_client):
        resp = api_client.get(reverse("api:measurements-example-measurements-list"))
        assert resp.status_code == 200
