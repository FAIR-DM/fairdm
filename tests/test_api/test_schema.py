"""Tests for the generated OpenAPI schema (Feature 011 US5)."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from rest_framework.test import APIClient

#: Parameters every list takes from the pagination and ordering classes, not from a filter set.
LIST_PARAMETERS = {"ordering", "page", "page_size"}


@pytest.fixture
def schema(db):
    """Return the generated schema as the schema address serves it."""
    response = APIClient().get(reverse("api:api-schema"), {"format": "json"})
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def registered_types():
    """Return the registered sample and measurement types with their configurations."""
    from fairdm.registry import registry

    return [
        (model, registry.get_for_model(model))
        for model in (*registry.samples, *registry.measurements)
    ]


def detail_path(basename):
    """Return the schema path of a route's record address."""
    return reverse(f"api:{basename}-detail", kwargs={"uuid": "X"}).replace(
        "X", "{uuid}"
    )


@pytest.mark.django_db
class TestSchemaMatchesRoutes:
    def test_every_route_the_router_serves_has_a_path(self, schema):
        from fairdm.api.router import fairdm_api_router

        expected = set()
        for _prefix, _viewset, basename in fairdm_api_router.registry:
            expected.add(reverse(f"api:{basename}-list"))
            expected.add(detail_path(basename))

        assert expected
        assert expected <= set(schema["paths"])

    def test_both_catalogues_have_a_path(self, schema):
        assert reverse("api:api-sample-discovery") in schema["paths"]
        assert reverse("api:api-measurement-discovery") in schema["paths"]

    def test_every_registered_type_is_a_component(self, schema, registered_types):
        for model, _config in registered_types:
            assert model.__name__ in schema["components"]["schemas"]

    def test_a_components_properties_are_the_serializers_fields(
        self, schema, registered_types
    ):
        for model, config in registered_types:
            fields = config.get_serializer_class()().fields
            readable = {name for name, field in fields.items() if not field.write_only}

            properties = schema["components"]["schemas"][model.__name__]["properties"]

            assert set(properties) == readable, model.__name__

    def test_read_only_fields_are_marked_and_writable_ones_are_not(
        self, schema, registered_types
    ):
        for model, config in registered_types:
            fields = config.get_serializer_class()().fields
            properties = schema["components"]["schemas"][model.__name__]["properties"]

            for name, field in fields.items():
                if field.write_only:
                    continue
                marked = properties[name].get("readOnly", False)
                assert marked == field.read_only, f"{model.__name__}.{name}"

    def test_the_writable_fields_a_caller_must_send_are_required(
        self, schema, registered_types
    ):
        for model, config in registered_types:
            fields = config.get_serializer_class()().fields
            component = schema["components"]["schemas"][model.__name__]
            # A response always carries the read-only fields, so they are listed as well.
            required = set(component.get("required", []))

            must_send = {
                name
                for name, field in fields.items()
                if field.required and not field.read_only
            }
            writable = {name for name, field in fields.items() if not field.read_only}

            assert required & writable == must_send, model.__name__

    def test_a_list_offers_no_parameter_the_filter_set_drops_per_request(
        self, schema, registered_types, rf
    ):
        from rest_framework.request import Request

        from fairdm.api.filters import FairDMFilterBackend

        checked = 0
        for model, _config in registered_types:
            basename = self.basename(model)
            address = reverse(f"api:{basename}-list")
            viewset = self.viewset_of(address)
            request = Request(rf.get(address))
            request.user = AnonymousUser()
            view = viewset(request=request, format_kwarg=None)
            queryset = viewset.queryset.all()
            filterset_class = FairDMFilterBackend().get_filterset_class(view, queryset)
            dropped = set(filterset_class.base_filters) - set(
                filterset_class(data={}, queryset=queryset, request=request).filters
            )
            offered = {
                parameter["name"]
                for parameter in schema["paths"][address]["get"]["parameters"]
            }

            assert offered.isdisjoint(dropped), model.__name__
            checked += len(dropped)

        # Without a dropped filter in the demonstration types the test would prove nothing.
        assert checked

    def test_no_list_offers_a_content_type_filter(self, schema, registered_types):
        for model, _config in registered_types:
            address = reverse(f"api:{self.basename(model)}-list")

            offered = {
                parameter["name"]
                for parameter in schema["paths"][address]["get"]["parameters"]
            }

            assert "polymorphic_ctype" not in offered, model.__name__

    @staticmethod
    def basename(model):
        from fairdm.core.models import Sample

        prefix = "samples" if issubclass(model, Sample) else "measurements"
        slug = str(model._meta.verbose_name_plural).lower().replace(" ", "-")
        return f"{prefix}-{slug}"

    @staticmethod
    def viewset_of(address):
        from django.urls import resolve

        return resolve(address).func.cls


@pytest.mark.django_db
class TestSchemaDescribesThePortal:
    def test_the_security_schemes_are_the_token_header_and_the_session(self, schema):
        schemes = list(schema["components"]["securitySchemes"].values())

        header = [s for s in schemes if s["in"] == "header"]
        cookie = [s for s in schemes if s["in"] == "cookie"]
        assert [s["name"] for s in header] == ["Authorization"]
        assert len(cookie) == 1
        assert len(schemes) == 2

    def test_the_description_carries_each_configured_limit(self, schema, settings):
        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].values()

        assert rates
        for rate in rates:
            assert rate in schema["info"]["description"]

    def test_the_description_follows_a_changed_limit(self, settings):
        before = list(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].values())
        settings.REST_FRAMEWORK = {
            **settings.REST_FRAMEWORK,
            "DEFAULT_THROTTLE_RATES": {"spare": "7919/week", "other": "6841/minute"},
        }

        description = self.described()

        assert "7919/week" in description
        assert "6841/minute" in description
        assert not any(rate in description for rate in before)

    def test_the_description_carries_the_page_sizes(self, schema):
        from fairdm.api.pagination import FairDMPagination

        pagination = FairDMPagination()

        assert str(pagination.page_size) in schema["info"]["description"]
        assert str(pagination.max_page_size) in schema["info"]["description"]

    def test_the_description_follows_changed_page_sizes(self, monkeypatch):
        from fairdm.api.pagination import FairDMPagination

        monkeypatch.setattr(FairDMPagination, "page_size", 7927)
        monkeypatch.setattr(FairDMPagination, "max_page_size", 8209)

        description = self.described()

        assert "7927" in description
        assert "8209" in description

    def test_a_portal_without_paging_still_gets_a_description(self, settings):
        settings.REST_FRAMEWORK = {
            **settings.REST_FRAMEWORK,
            "DEFAULT_PAGINATION_CLASS": None,
        }

        assert self.described()

    def test_the_description_keeps_the_portals_own_text(self, monkeypatch):
        from drf_spectacular.settings import spectacular_settings

        monkeypatch.setattr(
            spectacular_settings, "DESCRIPTION", "A portal's own introduction."
        )

        assert self.described().startswith("A portal's own introduction.")

    @staticmethod
    def described():
        """Return the description of a schema generated now."""
        response = APIClient().get(reverse("api:api-schema"), {"format": "json"})
        assert response.status_code == 200
        return response.json()["info"]["description"]
