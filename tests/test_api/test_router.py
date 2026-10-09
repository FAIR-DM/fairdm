"""Tests for FairDM API router auto-registration and the API root (Feature 011 US1)."""

import pytest
from django.urls import resolve, reverse


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


@pytest.mark.django_db
class TestCustomViewset:
    @pytest.fixture
    def viewset(self):
        from fairdm.api.serializers import ProjectSerializer
        from fairdm.api.viewsets import BaseViewSet
        from fairdm.core.models import Project

        class FeaturedProjectViewSet(BaseViewSet):
            """Projects a portal highlights."""

            serializer_class = ProjectSerializer
            queryset = Project.objects.all()
            http_method_names = ["get"]

        return FeaturedProjectViewSet

    def test_a_viewset_registered_on_the_router_is_served(
        self, api_client, on_the_router, viewset, public_project
    ):
        on_the_router("featured", viewset, "featured")

        response = api_client.get(reverse("api:featured-list"))

        assert response.status_code == 200
        assert str(public_project.uuid) in [
            row["uuid"] for row in response.json()["results"]
        ]

    def test_it_is_served_beside_the_generated_routes(
        self, api_client, on_the_router, viewset
    ):
        on_the_router("featured", viewset, "featured")

        assert api_client.get(reverse("api:featured-list")).status_code == 200
        assert api_client.get(reverse("api:project-list")).status_code == 200
        assert (
            api_client.get(reverse("api:samples-rock-samples-list")).status_code == 200
        )

    def test_it_appears_in_the_generated_schema(
        self, api_client, on_the_router, viewset
    ):
        on_the_router("featured", viewset, "featured")

        response = api_client.get(reverse("api:api-schema"), {"format": "json"})

        assert response.status_code == 200
        assert "/api/v1/featured/" in response.json()["paths"]


class TestRegistrationFailureIsReported:
    @pytest.fixture
    def off_the_base(self):
        from rest_framework import serializers

        class OffTheBase(serializers.ModelSerializer):
            class Meta:
                fields = ["name"]

        return OffTheBase

    def test_a_type_whose_endpoints_cannot_be_built_stops_the_registration(
        self, monkeypatch, off_the_base
    ):
        from django.core.exceptions import ImproperlyConfigured

        from demo.models import RockSample
        from fairdm.api.router import FairDMAPIRouter
        from fairdm.registry import ModelConfiguration, registry

        off_the_base.Meta.model = RockSample
        monkeypatch.setitem(
            registry._registry,
            RockSample,
            ModelConfiguration(model=RockSample, serializer_class=off_the_base),
        )

        with pytest.raises(ImproperlyConfigured):
            FairDMAPIRouter().register_types()

    def test_a_measurement_type_whose_endpoints_cannot_be_built_stops_it_too(
        self, monkeypatch, off_the_base
    ):
        from django.core.exceptions import ImproperlyConfigured

        from demo.models import XRFMeasurement
        from fairdm.api.router import FairDMAPIRouter
        from fairdm.registry import ModelConfiguration, registry

        off_the_base.Meta.model = XRFMeasurement
        monkeypatch.setitem(
            registry._registry,
            XRFMeasurement,
            ModelConfiguration(model=XRFMeasurement, serializer_class=off_the_base),
        )

        with pytest.raises(ImproperlyConfigured):
            FairDMAPIRouter().register_types()

    def test_a_failure_that_is_not_a_configuration_error_is_not_swallowed_either(
        self, monkeypatch
    ):
        from demo.models import RockSample
        from fairdm.api.router import FairDMAPIRouter
        from fairdm.registry import ModelConfiguration, registry

        class Failing(ModelConfiguration):
            def get_serializer_class(self):
                raise RuntimeError("the serializer cannot be built")

        monkeypatch.setitem(registry._registry, RockSample, Failing(model=RockSample))

        with pytest.raises(RuntimeError, match="cannot be built"):
            FairDMAPIRouter().register_types()

    def test_a_filter_set_that_cannot_be_built_stops_the_registration(
        self, monkeypatch
    ):
        from demo.models import RockSample
        from fairdm.api.router import FairDMAPIRouter
        from fairdm.registry import ModelConfiguration, registry

        class Failing(ModelConfiguration):
            def get_filterset_class(self):
                raise RuntimeError("the filter set cannot be built")

        monkeypatch.setitem(registry._registry, RockSample, Failing(model=RockSample))

        with pytest.raises(RuntimeError, match="cannot be built"):
            FairDMAPIRouter().register_types()


class TestAddresses:
    @pytest.fixture
    def routes(self):
        """Return the router's prefixes and names after it registers the registered types."""
        from fairdm.api.router import FairDMAPIRouter

        def routes():
            router = FairDMAPIRouter()
            router.register_types()
            return {basename: prefix for prefix, _viewset, basename in router.registry}

        return routes

    def test_a_samples_address_is_its_plural_name_under_samples(self, routes):
        assert routes()["samples-rock-samples"] == "samples/rock-samples"

    def test_a_measurements_address_is_its_plural_name_under_measurements(self, routes):
        assert routes()["measurements-xrf-measurements"] == (
            "measurements/xrf-measurements"
        )

    @pytest.mark.django_db
    def test_the_generated_routes_are_served_at_those_addresses(self):
        assert (
            reverse("api:samples-rock-samples-list") == "/api/v1/samples/rock-samples/"
        )
        assert reverse("api:measurements-xrf-measurements-list") == (
            "/api/v1/measurements/xrf-measurements/"
        )

    def test_every_registered_type_has_a_route(self, routes):
        from fairdm.registry import registry

        assert len(routes()) == len(registry.samples) + len(registry.measurements)

    def test_a_sample_type_and_a_measurement_type_with_one_plural_name_get_different_names(
        self, monkeypatch
    ):
        from demo.models import RockSample, XRFMeasurement
        from fairdm.api.router import FairDMAPIRouter

        monkeypatch.setattr(RockSample._meta, "verbose_name_plural", "readings")
        monkeypatch.setattr(XRFMeasurement._meta, "verbose_name_plural", "readings")
        router = FairDMAPIRouter()

        router.register_types()

        named = {basename: prefix for prefix, _viewset, basename in router.registry}
        assert named["samples-readings"] == "samples/readings"
        assert named["measurements-readings"] == "measurements/readings"

    def test_renaming_a_types_plural_name_moves_its_address(self, monkeypatch):
        from demo.models import RockSample
        from fairdm.api.router import FairDMAPIRouter

        monkeypatch.setattr(RockSample._meta, "verbose_name_plural", "Hand Specimens")
        router = FairDMAPIRouter()

        router.register_types()

        named = {basename: prefix for prefix, _viewset, basename in router.registry}
        assert named["samples-hand-specimens"] == "samples/hand-specimens"
        assert "samples-rock-samples" not in named


@pytest.mark.django_db
class TestRoot:
    @pytest.fixture
    def links(self, api_client):
        response = api_client.get(
            reverse("api:api-root"), HTTP_ACCEPT="application/json"
        )
        assert response.status_code == 200
        return response.json()

    def test_the_root_links_to_every_list_route(self, links):
        from fairdm.api.router import fairdm_api_router

        linked = set(links.values())

        for _prefix, _viewset, basename in fairdm_api_router.registry:
            assert f"http://testserver{reverse(f'api:{basename}-list')}" in linked

    def test_the_router_is_the_one_the_portal_serves(self):
        from rest_framework.routers import DefaultRouter

        from fairdm.api.router import FairDMAPIRouter, fairdm_api_router

        assert isinstance(fairdm_api_router, FairDMAPIRouter)
        assert isinstance(fairdm_api_router, DefaultRouter)

    def test_each_link_answers(self, api_client, links):
        for link in links.values():
            assert api_client.get(link).status_code == 200
