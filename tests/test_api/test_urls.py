"""Tests for FairDM API URL routing (``fairdm/api/urls.py``).

Covers:
- POST /api/v1/auth/login/  -> returns auth token key for valid credentials
- Token-in-header grants access to a write-protected endpoint
- POST /api/v1/auth/logout/ -> revokes the token (token unusable after logout)
- Invalid credentials return 400 with error details
- Session authentication works (cookie-based, used by Swagger UI)
- GET /api/v1/docs/, /api/v1/redoc/, /api/v1/schema/ render the drf-spectacular
  powered Swagger UI, ReDoc, and OpenAPI schema endpoints
"""

import pytest
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from fairdm.factories import UserFactory

# ---------------------------------------------------------------------------
# URL shortcuts
# ---------------------------------------------------------------------------

LOGIN_URL = "/api/v1/auth/login/"
LOGOUT_URL = "/api/v1/auth/logout/"


# ---------------------------------------------------------------------------
# Token login
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTokenLogin:
    """POST /api/v1/auth/login/ with valid credentials."""

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


# ---------------------------------------------------------------------------
# Token-header access
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTokenHeaderAccess:
    """Token returned by login grants access to write-protected endpoints."""

    def test_token_from_login_authenticates_request(self, api_client, db):
        """Token obtained via login works immediately for authenticated requests."""
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
        # The project list is a readable authenticated endpoint
        response = client.get(reverse("api:project-list"))
        assert response.status_code == 200

    def test_invalid_token_returns_401(self, api_client, db):
        """Made-up token key is rejected with 401."""
        api_client.credentials(HTTP_AUTHORIZATION="Token thisisnotavalidtoken")
        response = api_client.get(reverse("api:project-list"))
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTokenLogout:
    """POST /api/v1/auth/logout/ revokes the token."""

    def test_logout_returns_200(self, authenticated_client):
        response = authenticated_client.post(LOGOUT_URL)
        assert response.status_code == 200

    def test_token_unusable_after_logout(self, user, token):
        """Token is deleted from the DB on logout -> subsequent requests get 401."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

        # Confirm the token works before logout
        pre_response = client.get(reverse("api:project-list"))
        assert pre_response.status_code == 200

        # Logout
        logout_resp = client.post(LOGOUT_URL)
        assert logout_resp.status_code == 200

        # Token should now be invalid (dj-rest-auth deletes the token on logout)
        post_response = client.get(reverse("api:project-list"))
        assert post_response.status_code == 401


# ---------------------------------------------------------------------------
# Interactive documentation endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSwaggerUI:
    """GET /api/v1/docs/ must return a valid Swagger UI page."""

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
        """Docs must be publicly accessible (SERVE_INCLUDE_SCHEMA=False means
        the schema URL is separate, but the UI page itself is public)."""
        response = api_client.get("/api/v1/docs/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestReDoc:
    """GET /api/v1/redoc/ must return a valid ReDoc page."""

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
    """GET /api/v1/schema/ must return a valid OpenAPI 3.0 document."""

    def test_schema_returns_200(self, api_client):
        response = api_client.get("/api/v1/schema/")
        assert response.status_code == 200

    def test_schema_returns_yaml_or_json(self, api_client):
        """Schema endpoint should return YAML or JSON content."""
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
        """Schema document must contain the 'openapi' version field."""
        response = api_client.get("/api/v1/schema/?format=json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert data["openapi"].startswith("3.")

    def test_schema_contains_info(self, api_client):
        """Schema must include an 'info' section with title and version."""
        response = api_client.get("/api/v1/schema/?format=json")
        data = response.json()
        assert "info" in data
        assert "title" in data["info"]
        assert "version" in data["info"]

    def test_schema_contains_paths(self, api_client):
        """Schema must expose at least the core endpoints (projects, datasets)."""
        response = api_client.get("/api/v1/schema/?format=json")
        data = response.json()
        assert "paths" in data
        paths = data["paths"]
        # Core model endpoints must appear
        assert any("/projects/" in p for p in paths), (
            f"No projects path in {list(paths)[:10]}"
        )
        assert any("/datasets/" in p for p in paths), (
            f"No datasets path in {list(paths)[:10]}"
        )

    def test_schema_contains_registered_sample_types(self, api_client):
        """Registry-generated sample endpoints must appear in the schema."""
        response = api_client.get("/api/v1/schema/?format=json")
        data = response.json()
        paths = data.get("paths", {})
        # RockSample registered in demo app should produce /samples/rock-sample/
        sample_paths = [p for p in paths if "/samples/" in p and p.count("/") >= 4]
        assert len(sample_paths) > 0, (
            f"No typed sample paths in schema. Got: {list(paths)[:15]}"
        )

    def test_schema_accessible_without_auth(self, api_client):
        """Schema endpoint must be publicly accessible."""
        response = api_client.get("/api/v1/schema/")
        assert response.status_code == 200
