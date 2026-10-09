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

    def test_every_operation_refers_to_a_scheme_the_schema_defines(self, schema):
        defined = set(schema["components"]["securitySchemes"])
        referred = set()
        for path in schema["paths"].values():
            for operation in path.values():
                for requirement in operation.get("security", []):
                    referred |= set(requirement)

        assert "tokenAuth" in referred
        assert referred <= defined

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

    def test_the_description_carries_the_page_sizes_the_settings_hold(self, settings):
        settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "PAGE_SIZE": 7927}
        settings.FAIRDM_API_MAX_PAGE_SIZE = 8209

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


def registration_text(config):
    """Return the description a registration gives its type, or an empty string."""
    if config.metadata and config.metadata.description:
        return str(config.metadata.description)
    return str(config.description or "")


def every_description(node):
    """Yield each ``description`` text found anywhere in a part of the schema."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "description" and isinstance(value, str):
                yield value
            else:
                yield from every_description(value)
    elif isinstance(node, list):
        for value in node:
            yield from every_description(value)


@pytest.mark.django_db
class TestTypesInTheDocumentation:
    #: The headings of the first schema, which the interactive page reads.
    HEADINGS = ("Projects", "Datasets", "Contributors", "Samples", "Measurements")

    @pytest.fixture
    def tags(self, schema):
        """Return the schema's top-level tags by name."""
        return {tag["name"]: tag for tag in schema.get("tags", [])}

    @staticmethod
    def plural(model):
        return str(model._meta.verbose_name_plural)

    @staticmethod
    def heading(model):
        from fairdm.core.models import Sample

        return "Samples" if issubclass(model, Sample) else "Measurements"

    @staticmethod
    def operations(schema, model):
        """Return ``(path, method, operation)`` for each operation of a registered type."""
        basename = TestSchemaMatchesRoutes.basename(model)
        for path in (reverse(f"api:{basename}-list"), detail_path(basename)):
            for method, operation in schema["paths"][path].items():
                yield path, method, operation

    @staticmethod
    def list_operation(schema, model):
        basename = TestSchemaMatchesRoutes.basename(model)
        return schema["paths"][reverse(f"api:{basename}-list")]["get"]

    def test_projects_datasets_and_contributors_are_described_with_their_viewsets_words(
        self, tags
    ):
        import inspect

        from fairdm.api.viewsets import (
            ContributorViewSet,
            DatasetViewSet,
            ProjectViewSet,
        )

        for name, viewset in (
            ("Projects", ProjectViewSet),
            ("Datasets", DatasetViewSet),
            ("Contributors", ContributorViewSet),
        ):
            assert tags[name]["description"] == inspect.getdoc(viewset)

    def test_every_operation_of_a_type_keeps_the_types_description(
        self, schema, registered_types
    ):
        checked = 0
        for model, config in registered_types:
            text = registration_text(config)
            if not text:
                continue
            for path, method, operation in self.operations(schema, model):
                assert operation["description"].startswith(text), (path, method)
                checked += 1

        assert checked

    def test_a_list_operation_carries_what_the_registration_gives(
        self, schema, registered_types
    ):
        given = set()
        for model, config in registered_types:
            metadata = config.metadata
            description = self.list_operation(schema, model)["description"]
            texts = [registration_text(config)]
            if metadata and metadata.authority:
                authority = metadata.authority
                texts += [authority.name, authority.short_name, authority.website]
                given.add("authority")
            if metadata and metadata.citation:
                texts += [metadata.citation.text, metadata.citation.doi]
                given.add("citation")
            if metadata:
                texts += metadata.keywords
                given.add("keywords") if metadata.keywords else None

            for text in filter(None, texts):
                assert str(text) in description, (model.__name__, text)

        assert given == {"authority", "citation", "keywords"}

    def test_a_list_operation_links_to_the_repository_where_the_registration_gives_one(
        self, schema, registered_types
    ):
        linked = 0
        for model, config in registered_types:
            operation = self.list_operation(schema, model)
            url = config.metadata.repository_url if config.metadata else ""
            if url:
                assert operation["externalDocs"]["url"] == url
                linked += 1
            else:
                assert "externalDocs" not in operation

        assert linked

    def test_a_maintainers_details_are_never_published(
        self, api_client, monkeypatch, registered_types
    ):
        import dataclasses

        config = next(
            c for _model, c in registered_types if c.metadata and c.metadata.authority
        )
        monkeypatch.setattr(
            config,
            "metadata",
            dataclasses.replace(
                config.metadata,
                maintainer="Maintainer Person",
                maintainer_email="maintainer@example.org",
            ),
        )

        body = api_client.get(reverse("api:api-schema"), {"format": "json"}).text

        assert "Maintainer Person" not in body
        assert "maintainer@example.org" not in body

    def test_a_types_record_is_described_in_the_types_words_and_titled_with_its_name(
        self, schema, registered_types
    ):
        checked = 0
        for model, config in registered_types:
            for name in (model.__name__, f"Patched{model.__name__}"):
                component = schema["components"]["schemas"][name]

                assert component["title"] == str(model._meta.verbose_name)
                if registration_text(config):
                    assert component["description"] == registration_text(config)
                    checked += 1

        assert checked

    def test_no_description_is_a_docstring_of_a_base_class(self, schema):
        import inspect

        from fairdm.api.serializers import (
            BaseMeasurementSerializer,
            BaseSampleSerializer,
            RecordSerializer,
        )
        from fairdm.api.viewsets import BaseViewSet

        first_lines = [
            inspect.getdoc(base).splitlines()[0]
            for base in (
                BaseSampleSerializer,
                BaseMeasurementSerializer,
                RecordSerializer,
                BaseViewSet,
            )
        ]

        for text in every_description(schema):
            assert ":class:" not in text
            for line in first_lines:
                assert line not in text


@pytest.mark.django_db
class TestMetadataDescriptionComesFirst:
    def test_a_type_with_its_own_metadata_description_is_not_given_its_base_s(self):
        from demo.models import XRFMeasurement
        from fairdm.registry import registry

        config = registry.get_for_model(XRFMeasurement)
        own = str(config.metadata.description)
        assert own
        assert own != str(config.description)

        schema = APIClient().get(reverse("api:api-schema"), {"format": "json"}).json()
        basename = TestSchemaMatchesRoutes.basename(XRFMeasurement)
        operation = schema["paths"][reverse(f"api:{basename}-list")]["get"]

        assert operation["description"].startswith(own)
