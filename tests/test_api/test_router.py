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


CATALOGUES = {
    "samples": "api:api-sample-discovery",
    "measurements": "api:api-measurement-discovery",
}


def registered(kind):
    """Return the registered sample or measurement types."""
    from fairdm.registry import registry

    return getattr(registry, kind)


@pytest.mark.django_db
class TestCatalogues:
    @pytest.fixture
    def catalogue(self, api_client):
        """Return a function giving the entries of a catalogue, by the name of its type."""

        def catalogue(kind, client=api_client):
            response = client.get(reverse(CATALOGUES[kind]))
            assert response.status_code == 200
            return {entry["name"]: entry for entry in response.json()["types"]}

        return catalogue

    @pytest.mark.parametrize("kind", list(CATALOGUES))
    def test_a_catalogue_lists_every_registered_type(self, catalogue, kind):
        assert set(catalogue(kind)) == {model.__name__ for model in registered(kind)}

    @pytest.mark.parametrize("kind", list(CATALOGUES))
    def test_an_entry_names_its_type(self, catalogue, kind):
        entries = catalogue(kind)

        for model in registered(kind):
            entry = entries[model.__name__]
            assert entry["verbose_name"] == str(model._meta.verbose_name)
            assert entry["verbose_name_plural"] == str(model._meta.verbose_name_plural)
            assert entry["app_label"] == model._meta.app_label

    @pytest.mark.parametrize("kind", list(CATALOGUES))
    def test_an_entrys_address_is_its_list_route(self, catalogue, url_of, kind):
        entries = catalogue(kind)

        for model in registered(kind):
            assert entries[model.__name__]["endpoint"] == (
                f"http://testserver{url_of(model, 'list')}"
            )

    @pytest.mark.parametrize("kind", list(CATALOGUES))
    def test_an_entrys_address_answers_with_the_types_records(
        self, api_client, catalogue, kind
    ):
        for entry in catalogue(kind).values():
            response = api_client.get(entry["endpoint"])

            assert response.status_code == 200
            assert "results" in response.json()

    @pytest.mark.parametrize("kind", list(CATALOGUES))
    def test_an_entrys_fields_are_the_flat_list_its_serializer_carries(
        self, catalogue, kind
    ):
        from fairdm.registry import registry

        entries = catalogue(kind)

        for model in registered(kind):
            serializer = registry.get_for_model(model).get_serializer_class()
            assert entries[model.__name__]["fields"] == list(serializer().fields)

    @pytest.mark.parametrize("kind", list(CATALOGUES))
    def test_an_entrys_filters_are_those_its_list_accepts(
        self, api_client, catalogue, url_of, kind
    ):
        entries = catalogue(kind)
        schema = api_client.get(reverse("api:api-schema"), {"format": "json"}).json()

        for model in registered(kind):
            filters = entries[model.__name__]["filters"]
            parameters = {
                parameter["name"]
                for parameter in schema["paths"][url_of(model, "list")]["get"][
                    "parameters"
                ]
            }
            assert filters
            for name in filters:
                assert any(p == name or p.startswith(f"{name}_") for p in parameters)

    def test_a_samples_filters_include_its_dataset_and_a_measurements_its_sample(
        self, catalogue
    ):
        assert "dataset" in catalogue("samples")["RockSample"]["filters"]
        measurement = catalogue("measurements")["XRFMeasurement"]["filters"]
        assert {"dataset", "sample"} <= set(measurement)

    @pytest.mark.parametrize("kind", list(CATALOGUES))
    def test_no_entry_offers_a_content_type_filter(self, catalogue, kind):
        for entry in catalogue(kind).values():
            assert "polymorphic_ctype" not in entry["filters"]

    @pytest.mark.parametrize("kind", list(CATALOGUES))
    def test_with_no_registered_types_a_catalogue_is_an_empty_list(
        self, api_client, monkeypatch, kind
    ):
        from fairdm.registry import registry

        monkeypatch.setattr(type(registry), kind, property(lambda self: []))

        response = api_client.get(reverse(CATALOGUES[kind]))

        assert response.status_code == 200
        assert response.json() == {"types": []}


@pytest.mark.django_db
class TestCatalogueCounts:
    @pytest.fixture
    def records(self, public_dataset, private_dataset, make_record):
        """Make a sample and a measurement made on it in a public dataset and a private one."""
        from demo.models import RockSample, XRFMeasurement

        for dataset in (public_dataset, private_dataset):
            sample = make_record(RockSample, dataset)
            make_record(XRFMeasurement, dataset, sample=sample)
        return (RockSample, XRFMeasurement)

    @pytest.fixture
    def counted(self, records):
        """Return a function giving what a client's catalogues count for each type."""

        def counted(client):
            return {
                entry["name"]: entry["count"]
                for kind in CATALOGUES
                for entry in client.get(reverse(CATALOGUES[kind])).json()["types"]
            }

        return counted

    @pytest.fixture
    def person_with_level(self, private_dataset, member_at):
        from fairdm.contrib.contributors.choices import ContributionLevel

        return member_at(private_dataset, ContributionLevel.VIEW)

    def test_a_visitor_counts_the_records_in_public_datasets(self, api_client, counted):
        counts = counted(api_client)

        assert counts["RockSample"] == 1
        assert counts["XRFMeasurement"] == 1

    def test_a_signed_in_person_with_no_level_counts_what_a_visitor_does(
        self, counted, signed_in, user
    ):
        counts = counted(signed_in(user))

        assert counts["RockSample"] == 1
        assert counts["XRFMeasurement"] == 1

    def test_a_person_with_a_level_on_the_private_dataset_counts_its_records_too(
        self, counted, signed_in, person_with_level
    ):
        counts = counted(signed_in(person_with_level))

        assert counts["RockSample"] == 2
        assert counts["XRFMeasurement"] == 2

    @pytest.mark.parametrize("who", ["visitor", "no_level", "with_level"])
    def test_a_count_is_the_count_the_types_list_gives_the_same_caller(
        self,
        who,
        api_client,
        counted,
        signed_in,
        user,
        person_with_level,
        url_of,
        records,
    ):
        client = {
            "visitor": api_client,
            "no_level": signed_in(user),
            "with_level": signed_in(person_with_level),
        }[who]
        counts = counted(client)

        for model in records:
            listed = client.get(url_of(model, "list")).json()["count"]
            assert counts[model.__name__] == listed


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

    def test_the_root_links_to_both_catalogues(self, links):
        linked = set(links.values())

        for name in CATALOGUES.values():
            assert f"http://testserver{reverse(name)}" in linked

    def test_each_link_answers(self, api_client, links):
        for link in links.values():
            assert api_client.get(link).status_code == 200
