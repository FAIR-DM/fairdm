"""Tests for Feature 011 US2: Interactive API Documentation.

Verifies that drf-spectacular-powered Swagger UI, ReDoc, and OpenAPI schema
endpoints render correctly and reflect all registered model endpoints.
"""

import pytest


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
            for ct in ("application/vnd.oai.openapi", "application/json", "application/yaml")
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
        assert any("/projects/" in p for p in paths), f"No projects path in {list(paths)[:10]}"
        assert any("/datasets/" in p for p in paths), f"No datasets path in {list(paths)[:10]}"

    def test_schema_contains_registered_sample_types(self, api_client):
        """Registry-generated sample endpoints must appear in the schema."""
        response = api_client.get("/api/v1/schema/?format=json")
        data = response.json()
        paths = data.get("paths", {})
        # RockSample registered in demo app should produce /samples/rock-sample/
        sample_paths = [p for p in paths if "/samples/" in p and p.count("/") >= 4]
        assert len(sample_paths) > 0, f"No typed sample paths in schema. Got: {list(paths)[:15]}"

    def test_schema_accessible_without_auth(self, api_client):
        """Schema endpoint must be publicly accessible."""
        response = api_client.get("/api/v1/schema/")
        assert response.status_code == 200
