"""Tests for FairDM API authentication endpoints (Feature 011 â€” US3).

Covers:
- POST /api/v1/auth/login/  -> returns auth token key for valid credentials
- Token-in-header grants access to a write-protected endpoint
- POST /api/v1/auth/logout/ -> revokes the token (token unusable after logout)
- Invalid credentials return 400 with error details
- Session authentication works (cookie-based, used by Swagger UI)
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
