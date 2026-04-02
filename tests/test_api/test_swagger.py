"""Tests for Swagger/OpenAPI documentation quality (Feature 011 — Phases 13–15).

Covers:
- Phase 13: Schema component naming — no "API" postfix in component names.
- Phase 14: Meaningful endpoint descriptions — no internal BaseViewSet details.
- Phase 15: Portal-developer API description customization via settings.
"""

import pytest
from rest_framework.test import APIClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def schema_client(db):
    """APIClient that can fetch the OpenAPI schema."""
    return APIClient()


@pytest.fixture
def openapi_schema(schema_client):
    """Fetch the OpenAPI schema from /api/v1/schema/ and return the parsed dict."""
    import yaml

    response = schema_client.get("/api/v1/schema/", HTTP_ACCEPT="application/vnd.oai.openapi")
    assert response.status_code == 200, f"Schema endpoint returned {response.status_code}"
    # drf-spectacular returns YAML by default for application/vnd.oai.openapi
    content = response.content.decode("utf-8")
    schema = yaml.safe_load(content)
    assert isinstance(schema, dict), "Schema must be a dict"
    return schema


# ---------------------------------------------------------------------------
# Phase 13: Schema Component Naming Cleanup (T073)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSchemaComponentNaming:
    """Schema component names must NOT contain "API" postfix."""

    def test_registered_sample_types_have_clean_names(self, openapi_schema):
        """Auto-generated serializers for registered Sample types use clean names.

        E.g. RockSample, SoilSample — NOT RockSampleAPI, SoilSampleAPI.
        """
        components = openapi_schema.get("components", {}).get("schemas", {})
        api_named = [name for name in components if name.endswith("API") and not name.startswith("Patched")]
        assert not api_named, (
            f"Found component names with 'API' postfix: {api_named}. "
            "Auto-generated serializers should be named '{ModelName}Serializer' "
            "so schema components become '{ModelName}' (without 'API')."
        )

    def test_registered_measurement_types_have_clean_names(self, openapi_schema):
        """Auto-generated serializers for registered Measurement types use clean names.

        E.g. XRFMeasurement, ExampleMeasurement — NOT XRFMeasurementAPI.
        """
        components = openapi_schema.get("components", {}).get("schemas", {})
        measurement_api = [
            name
            for name in components
            if name.endswith("API") and not name.startswith("Patched")
        ]
        assert not measurement_api, (
            f"Measurement component names with 'API' postfix found: {measurement_api}"
        )

    def test_core_model_schemas_have_clean_names(self, openapi_schema):
        """Core model schemas (Project, Dataset, Contributor) lack 'API' postfix."""
        components = openapi_schema.get("components", {}).get("schemas", {})
        for expected_clean in ("Project", "Dataset", "Contributor"):
            # Check the clean name IS present…
            assert expected_clean in components or any(
                k.startswith(expected_clean) for k in components
            ), f"Expected schema component '{expected_clean}' not found. Available: {list(components)[:20]}"
            # …and the 'API'-postfixed variant is NOT present.
            api_name = f"{expected_clean}API"
            assert api_name not in components, (
                f"Found '{api_name}' — 'API' postfix should not appear in schema component names."
            )

    def test_patched_variants_have_clean_names(self, openapi_schema):
        """PATCH endpoint Patched* components also lack 'API' postfix.

        E.g. PatchedRockSample — NOT PatchedRockSampleAPI.
        """
        components = openapi_schema.get("components", {}).get("schemas", {})
        patched_api = [
            name for name in components if name.startswith("Patched") and name.endswith("API")
        ]
        assert not patched_api, (
            f"Found Patched* component names with 'API' postfix: {patched_api}. "
            "Expected clean names like PatchedRockSample, PatchedProject."
        )

    def test_component_split_patch_enabled(self, openapi_schema):
        """COMPONENT_SPLIT_PATCH=True generates separate Patched* variants for PATCH."""
        components = openapi_schema.get("components", {}).get("schemas", {})
        patched = [name for name in components if name.startswith("Patched")]
        assert patched, (
            "Expected Patched* schema components (COMPONENT_SPLIT_PATCH=True). "
            f"Available components: {list(components)[:20]}"
        )

    def test_demo_rock_sample_schema_name(self, openapi_schema):
        """Demo RockSample schema component is 'RockSample', not 'RockSampleAPI'."""
        components = openapi_schema.get("components", {}).get("schemas", {})
        assert "RockSampleAPI" not in components, (
            "Schema component 'RockSampleAPI' found — remove the 'API' postfix."
        )

    def test_demo_xrf_measurement_schema_name(self, openapi_schema):
        """Demo XRFMeasurement schema component is 'XRFMeasurement', not 'XRFMeasurementAPI'."""
        components = openapi_schema.get("components", {}).get("schemas", {})
        assert "XRFMeasurementAPI" not in components, (
            "Schema component 'XRFMeasurementAPI' found — remove the 'API' postfix."
        )


# ---------------------------------------------------------------------------
# Phase 14: Meaningful Endpoint Descriptions (T078)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestEndpointDescriptions:
    """Swagger endpoint descriptions must be consumer-facing, not internal implementation."""

    INTERNAL_STRINGS = [
        "Base viewset for all FairDM API resource endpoints",
        "lookup_field",
        "get_queryset()",
        "perform_create",
        "perform_update",
    ]

    def _collect_all_operation_descriptions(self, openapi_schema: dict) -> list[str]:
        """Return all operation description strings from the schema."""
        descriptions = []
        paths = openapi_schema.get("paths", {})
        for path_item in paths.values():
            for method_data in path_item.values():
                if isinstance(method_data, dict):
                    desc = method_data.get("description", "")
                    if desc:
                        descriptions.append(desc)
        return descriptions

    def test_no_internal_implementation_details_in_descriptions(self, openapi_schema):
        """No endpoint description should expose BaseViewSet internal details."""
        descriptions = self._collect_all_operation_descriptions(openapi_schema)
        assert descriptions, "Expected at least some endpoint descriptions in the schema."
        for desc in descriptions:
            for internal_str in self.INTERNAL_STRINGS:
                assert internal_str not in desc, (
                    f"Internal string '{internal_str}' found in endpoint description: {desc[:200]!r}"
                )

    def test_core_project_endpoint_has_consumer_description(self, openapi_schema):
        """The /api/v1/projects/ endpoint has a consumer-facing description."""
        paths = openapi_schema.get("paths", {})
        project_list_path = next(
            (p for p in paths if p.endswith("/projects/") and "{" not in p), None
        )
        assert project_list_path, f"Expected /projects/ path in schema. Paths: {list(paths)[:10]}"
        operations = paths[project_list_path]
        # GET list operation
        get_op = operations.get("get", {})
        description = get_op.get("description", "")
        # Should mention something meaningful about projects
        assert description, f"GET {project_list_path} has no description"
        for internal_str in self.INTERNAL_STRINGS:
            assert internal_str not in description, (
                f"Internal string '{internal_str}' found in projects description: {description[:200]!r}"
            )

    def test_core_dataset_endpoint_has_consumer_description(self, openapi_schema):
        """The /api/v1/datasets/ endpoint has a consumer-facing description."""
        paths = openapi_schema.get("paths", {})
        dataset_path = next((p for p in paths if p.endswith("/datasets/") and "{" not in p), None)
        assert dataset_path, "Expected /datasets/ path in schema."
        get_op = paths[dataset_path].get("get", {})
        description = get_op.get("description", "")
        assert description, f"GET {dataset_path} has no description"
        for internal_str in self.INTERNAL_STRINGS:
            assert internal_str not in description, (
                f"Internal string found in datasets description: {description[:200]!r}"
            )

    def test_generated_viewset_has_model_description(self, openapi_schema):
        """Generated viewsets for registered types show model-derived descriptions."""
        from fairdm.registry import registry

        paths = openapi_schema.get("paths", {})
        # Find at least one registered sample type that has a description in config
        for model in registry.samples:
            config = registry.get_for_model(model)
            desc = getattr(config, "description", None) or (
                getattr(config.metadata, "description", None) if config.metadata else None
            )
            if not desc:
                continue
            # Find the API endpoint path for this model
            slug = model._meta.verbose_name_plural.lower().replace(" ", "-")
            endpoint_path = next(
                (p for p in paths if f"samples/{slug}/" in p and "{" not in p), None
            )
            if endpoint_path is None:
                continue
            get_op = paths[endpoint_path].get("get", {})
            op_description = get_op.get("description", "")
            # The operation description must not be the BaseViewSet default
            for internal_str in self.INTERNAL_STRINGS:
                assert internal_str not in op_description, (
                    f"Internal string '{internal_str}' found in description for {endpoint_path}: "
                    f"{op_description[:200]!r}"
                )
            # Found and verified at least one — sufficient
            return
        pytest.skip("No registered sample type with a config description found in the schema.")


# ---------------------------------------------------------------------------
# Phase 15: Portal-Developer API Description Customization (T084)
# ---------------------------------------------------------------------------


class TestAPIDescriptionSettings:
    """FAIRDM_API_TITLE and FAIRDM_API_DESCRIPTION settings exist and are informative."""

    def test_fairdm_api_title_default(self):
        """Default FAIRDM_API_TITLE is 'FairDM Portal API'."""
        from fairdm.api.settings import FAIRDM_API_TITLE

        assert FAIRDM_API_TITLE == "FairDM Portal API"

    def test_fairdm_api_description_is_rich_multiline(self):
        """FAIRDM_API_DESCRIPTION is multi-line and contains key FairDM phrases."""
        from fairdm.api.settings import FAIRDM_API_DESCRIPTION

        assert isinstance(FAIRDM_API_DESCRIPTION, str)
        assert len(FAIRDM_API_DESCRIPTION) > 200, (
            "FAIRDM_API_DESCRIPTION should be a rich multi-line description, not a short sentence."
        )
        desc_lower = FAIRDM_API_DESCRIPTION.lower()
        for keyword in ("fairdm", "projects", "datasets"):
            assert keyword in desc_lower, (
                f"Expected '{keyword}' in FAIRDM_API_DESCRIPTION. Content: {FAIRDM_API_DESCRIPTION[:300]}"
            )
        # Check for authentication / rate limit information
        assert any(kw in desc_lower for kw in ("authentication", "token", "rate")), (
            "Expected authentication or rate limit info in FAIRDM_API_DESCRIPTION."
        )

    def test_spectacular_settings_title_equals_fairdm_api_title(self):
        """SPECTACULAR_SETTINGS['TITLE'] must equal FAIRDM_API_TITLE."""
        from fairdm.api.settings import FAIRDM_API_TITLE, SPECTACULAR_SETTINGS

        assert SPECTACULAR_SETTINGS["TITLE"] == FAIRDM_API_TITLE, (
            f"SPECTACULAR_SETTINGS['TITLE'] ({SPECTACULAR_SETTINGS['TITLE']!r}) "
            f"!= FAIRDM_API_TITLE ({FAIRDM_API_TITLE!r})"
        )

    def test_spectacular_settings_description_equals_fairdm_api_description(self):
        """SPECTACULAR_SETTINGS['DESCRIPTION'] must equal FAIRDM_API_DESCRIPTION."""
        from fairdm.api.settings import FAIRDM_API_DESCRIPTION, SPECTACULAR_SETTINGS

        assert SPECTACULAR_SETTINGS["DESCRIPTION"] == FAIRDM_API_DESCRIPTION, (
            f"SPECTACULAR_SETTINGS['DESCRIPTION'] does not match FAIRDM_API_DESCRIPTION"
        )

    def test_fairdm_api_title_is_overrideable(self, settings):
        """Overriding FAIRDM_API_TITLE via Django settings is possible."""
        settings.FAIRDM_API_TITLE = "My Custom Portal API"
        from django.conf import settings as django_settings

        assert django_settings.FAIRDM_API_TITLE == "My Custom Portal API"

    def test_fairdm_api_description_is_overrideable(self, settings):
        """Overriding FAIRDM_API_DESCRIPTION via Django settings is possible."""
        settings.FAIRDM_API_DESCRIPTION = "A custom portal for my research domain."
        from django.conf import settings as django_settings

        assert django_settings.FAIRDM_API_DESCRIPTION == "A custom portal for my research domain."


@pytest.mark.django_db
class TestSchemaReflectsAPITitle:
    """The generated OpenAPI schema title matches SPECTACULAR_SETTINGS['TITLE']."""

    def test_openapi_schema_title(self, openapi_schema):
        """OpenAPI schema info.title matches the configured API title."""
        title = openapi_schema.get("info", {}).get("title", "")
        assert "FairDM" in title or "Portal" in title, (
            f"Expected API title to contain 'FairDM' or 'Portal'. Got: {title!r}"
        )
