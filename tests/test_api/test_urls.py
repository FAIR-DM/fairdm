"""Tests for FairDM API URL routing (``fairdm/api/urls.py``)."""

import pytest
from django.shortcuts import resolve_url
from django.test import Client
from django.urls import get_resolver, reverse
from knox.models import AuthToken
from rest_framework.test import APIClient

from fairdm.factories import UserFactory


@pytest.mark.django_db
class TestSwaggerUI:
    def test_swagger_returns_200(self, api_client):
        response = api_client.get("/api/v1/docs/")
        assert response.status_code == 200

    def test_swagger_returns_html(self, api_client):
        response = api_client.get("/api/v1/docs/")
        assert response.status_code == 200
        assert "text/html" in response["Content-Type"]

    def test_swagger_contains_swagger_ui(self, api_client):
        response = api_client.get("/api/v1/docs/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "swagger" in content.lower()

    def test_swagger_accessible_without_auth(self, api_client):
        response = api_client.get("/api/v1/docs/")
        assert response.status_code == 200

    def test_swagger_reads_the_schema(self, api_client):
        content = api_client.get("/api/v1/docs/").content.decode()

        assert reverse("api:api-schema") in content


@pytest.mark.django_db
class TestOneDocumentationPage:
    def test_no_second_documentation_page_or_schema_is_served(self, api_client):
        assert api_client.get("/api/v1/redoc/").status_code == 404
        assert api_client.get("/api/v1/schema/nested/").status_code == 404


@pytest.mark.django_db
class TestOpenAPISchema:
    def test_schema_returns_200(self, api_client):
        response = api_client.get("/api/v1/schema/")
        assert response.status_code == 200

    def test_schema_returns_yaml_or_json(self, api_client):
        response = api_client.get("/api/v1/schema/")
        content_type = response["Content-Type"]
        assert any(
            ct in content_type
            for ct in (
                "application/vnd.oai.openapi",
                "application/json",
                "application/yaml",
            )
        )

    def test_schema_contains_openapi_key(self, api_client):
        response = api_client.get("/api/v1/schema/?format=json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert data["openapi"].startswith("3.")

    def test_schema_contains_info(self, api_client):
        response = api_client.get("/api/v1/schema/?format=json")
        data = response.json()
        assert "info" in data
        assert "title" in data["info"]
        assert "version" in data["info"]

    def test_schema_contains_paths(self, api_client):
        response = api_client.get("/api/v1/schema/?format=json")
        data = response.json()
        assert "paths" in data
        paths = data["paths"]
        assert any("/projects/" in p for p in paths), (
            f"No projects path in {list(paths)[:10]}"
        )
        assert any("/datasets/" in p for p in paths), (
            f"No datasets path in {list(paths)[:10]}"
        )

    def test_schema_contains_registered_sample_types(self, api_client):
        response = api_client.get("/api/v1/schema/?format=json")
        data = response.json()
        paths = data.get("paths", {})
        sample_paths = [p for p in paths if "/samples/" in p and p.count("/") >= 4]
        assert len(sample_paths) > 0, (
            f"No typed sample paths in schema. Got: {list(paths)[:15]}"
        )

    def test_schema_accessible_without_auth(self, api_client):
        response = api_client.get("/api/v1/schema/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestTokenPages:
    @pytest.fixture
    def person(self):
        return UserFactory()

    @pytest.fixture
    def signed_in_client(self, person):
        client = Client()
        client.force_login(person)
        return client

    @pytest.fixture
    def pages(self, make_token, person):
        """The addresses of the three pages, with a token of the person's to revoke."""
        record, _value = make_token(person)
        return {
            "list": reverse("account_api_tokens"),
            "create": reverse("account_api_token_create"),
            "revoke": reverse("account_api_token_revoke", args=[record.token_key]),
        }

    def test_the_pages_open_for_a_signed_in_person(self, signed_in_client, pages):
        for address in pages.values():
            assert signed_in_client.get(address).status_code == 200, address

    def test_the_pages_send_a_visitor_to_sign_in(self, pages, settings):
        for address in pages.values():
            response = Client().get(address)

            assert response.status_code == 302, address
            assert response["Location"].startswith(resolve_url(settings.LOGIN_URL)), (
                address
            )

    def test_a_token_created_on_the_create_page_authenticates_a_request(
        self, signed_in_client, person
    ):
        created = signed_in_client.post(
            reverse("account_api_token_create"), {"lifetime": "30d"}
        )
        assert created.status_code == 302
        listing = signed_in_client.get(created["Location"])
        value = listing.context["new_token"]["value"]

        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f"Token {value}")
        response = api.get(reverse("api:project-list"))

        assert response.status_code == 200

    def test_a_revoked_token_stops_working(self, signed_in_client, make_token, person):
        record, value = make_token(person)
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f"Token {value}")
        assert api.get(reverse("api:project-list")).status_code == 200

        signed_in_client.post(
            reverse("account_api_token_revoke", args=[record.token_key])
        )

        assert api.get(reverse("api:project-list")).status_code == 401

    def test_at_the_token_limit_the_create_page_creates_nothing(
        self, signed_in_client, make_token, person, settings
    ):
        settings.REST_KNOX = {"TOKEN_LIMIT_PER_USER": 2}
        make_token(person)
        make_token(person)

        signed_in_client.post(reverse("account_api_token_create"), {"lifetime": "30d"})

        assert AuthToken.objects.filter(user=person).count() == 2


@pytest.mark.django_db
class TestNoAccountEndpoints:
    FORBIDDEN = ("login", "logout", "password", "registration", "auth/user")

    @staticmethod
    def walk(resolver, prefix=""):
        """Yield the name and full path of every route under a resolver."""
        for entry in resolver.url_patterns:
            path = prefix + str(entry.pattern)
            if hasattr(entry, "url_patterns"):
                yield from TestNoAccountEndpoints.walk(entry, path)
            else:
                yield entry.name or "", path

    @pytest.fixture
    def routes(self):
        prefix, resolver = get_resolver().namespace_dict["api"]
        return list(self.walk(resolver, prefix))

    def test_the_api_has_routes_to_walk(self, routes):
        assert len(routes) > 10

    def test_no_route_name_or_path_belongs_to_an_account(self, routes):
        found = [
            (name, path)
            for name, path in routes
            for word in self.FORBIDDEN
            if word in name.lower() or word in path.lower()
        ]

        assert found == []

    def test_an_email_and_password_posted_to_the_old_login_address_find_nothing(
        self, api_client, db
    ):
        user = UserFactory(password="SecurePass123!")

        response = api_client.post(
            "/api/v1/auth/login/",
            {"email": user.email, "password": "SecurePass123!"},
            format="json",
        )

        assert response.status_code == 404
