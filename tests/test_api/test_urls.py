"""Tests for FairDM API URL routing (``fairdm/api/urls.py``)."""

import pytest
from django.test import Client
from django.urls import reverse
from knox.models import AuthToken
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from fairdm.factories import UserFactory

LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"


@pytest.mark.django_db
class TestTokenLogin:
    def test_login_returns_200(self, api_client, db):
        password = "SecurePass123!"
        user = UserFactory(password=password)
        response = api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": password},
            format="json",
        )
        assert response.status_code == 200

    def test_login_response_contains_token_key(self, api_client, db):
        password = "SecurePass123!"
        user = UserFactory(password=password)
        response = api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": password},
            format="json",
        )
        assert "key" in response.json()

    def test_login_token_key_matches_stored_token(self, api_client, db):
        password = "SecurePass123!"
        user = UserFactory(password=password)
        response = api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": password},
            format="json",
        )
        token = Token.objects.get(user=user)
        assert response.json()["key"] == token.key

    def test_invalid_credentials_return_400(self, api_client, db):
        user = UserFactory(password="correct_password")
        response = api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": "wrongpassword"},
            format="json",
        )
        assert response.status_code == 400

    def test_missing_credentials_return_400(self, api_client, db):
        response = api_client.post(LOGIN_URL, {}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestTokenHeaderAccess:
    def test_token_from_login_authenticates_request(self, api_client, db):
        password = "SecurePass123!"
        user = UserFactory(password=password)
        login_resp = api_client.post(
            LOGIN_URL,
            {"email": user.email, "password": password},
            format="json",
        )
        assert login_resp.status_code == 200
        token_key = login_resp.json()["key"]

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token_key}")
        response = client.get(reverse("api:project-list"))
        assert response.status_code == 200

    def test_invalid_token_returns_401(self, api_client, db):
        api_client.credentials(HTTP_AUTHORIZATION="Token thisisnotavalidtoken")
        response = api_client.get(reverse("api:project-list"))
        assert response.status_code == 401


@pytest.mark.django_db
class TestTokenLogout:
    def test_logout_returns_200(self, authenticated_client):
        response = authenticated_client.post(LOGOUT_URL)
        assert response.status_code == 200

    def test_token_unusable_after_logout(self, user, token):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        pre_response = client.get(reverse("api:project-list"))
        assert pre_response.status_code == 200

        logout_resp = client.post(LOGOUT_URL)
        assert logout_resp.status_code == 200

        # Token should now be invalid (dj-rest-auth deletes the token on logout)
        post_response = client.get(reverse("api:project-list"))
        assert post_response.status_code == 401


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


@pytest.mark.django_db
class TestReDoc:
    def test_redoc_returns_200(self, api_client):
        response = api_client.get("/api/v1/redoc/")
        assert response.status_code == 200

    def test_redoc_returns_html(self, api_client):
        response = api_client.get("/api/v1/redoc/")
        assert "text/html" in response["Content-Type"]

    def test_redoc_accessible_without_auth(self, api_client):
        response = api_client.get("/api/v1/redoc/")
        assert response.status_code == 200


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
            assert response["Location"].startswith(settings.LOGIN_URL), address

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
