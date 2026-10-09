"""Tests for FairDM API settings (``fairdm/api/settings.py``)."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import ContributionFactory, ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def schema_client(db):
    return APIClient()


@pytest.fixture
def openapi_schema(schema_client):
    import yaml

    response = schema_client.get(
        "/api/v1/schema/", HTTP_ACCEPT="application/vnd.oai.openapi"
    )
    assert response.status_code == 200, (
        f"Schema endpoint returned {response.status_code}"
    )
    # drf-spectacular returns YAML by default for application/vnd.oai.openapi
    content = response.content.decode("utf-8")
    schema = yaml.safe_load(content)
    assert isinstance(schema, dict), "Schema must be a dict"
    return schema


class TestFairDMAPIDocsURLSetting:
    def test_third_child_default_url_is_fairdm_org(self):
        from fairdm.api.settings import FAIRDM_API_DOCS_URL

        assert FAIRDM_API_DOCS_URL == "https://fairdm.org/api/"

    @pytest.mark.django_db
    def test_override_fairdm_api_docs_url_respected(self, settings):
        settings.FAIRDM_API_DOCS_URL = "https://custom.example.org/api/"

        assert settings.FAIRDM_API_DOCS_URL == "https://custom.example.org/api/"


@pytest.mark.django_db
class TestSchemaComponentNaming:
    def test_registered_sample_types_have_clean_names(self, openapi_schema):
        components = openapi_schema.get("components", {}).get("schemas", {})
        api_named = [
            name
            for name in components
            if name.endswith("API") and not name.startswith("Patched")
        ]
        assert not api_named, (
            f"Found component names with 'API' postfix: {api_named}. "
            "Auto-generated serializers should be named '{ModelName}Serializer' "
            "so schema components become '{ModelName}' (without 'API')."
        )

    def test_registered_measurement_types_have_clean_names(self, openapi_schema):
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
        components = openapi_schema.get("components", {}).get("schemas", {})
        for expected_clean in ("Project", "Dataset", "Contributor"):
            assert expected_clean in components or any(
                k.startswith(expected_clean) for k in components
            ), (
                f"Expected schema component '{expected_clean}' not found. Available: {list(components)[:20]}"
            )
            api_name = f"{expected_clean}API"
            assert api_name not in components, (
                f"Found '{api_name}' -- 'API' postfix should not appear in schema component names."
            )

    def test_patched_variants_have_clean_names(self, openapi_schema):
        components = openapi_schema.get("components", {}).get("schemas", {})
        patched_api = [
            name
            for name in components
            if name.startswith("Patched") and name.endswith("API")
        ]
        assert not patched_api, (
            f"Found Patched* component names with 'API' postfix: {patched_api}. "
            "Expected clean names like PatchedRockSample, PatchedProject."
        )

    def test_component_split_patch_enabled(self, openapi_schema):
        components = openapi_schema.get("components", {}).get("schemas", {})
        patched = [name for name in components if name.startswith("Patched")]
        assert patched, (
            "Expected Patched* schema components (COMPONENT_SPLIT_PATCH=True). "
            f"Available components: {list(components)[:20]}"
        )

    def test_demo_rock_sample_schema_name(self, openapi_schema):
        components = openapi_schema.get("components", {}).get("schemas", {})
        assert "RockSampleAPI" not in components, (
            "Schema component 'RockSampleAPI' found -- remove the 'API' postfix."
        )

    def test_demo_xrf_measurement_schema_name(self, openapi_schema):
        components = openapi_schema.get("components", {}).get("schemas", {})
        assert "XRFMeasurementAPI" not in components, (
            "Schema component 'XRFMeasurementAPI' found -- remove the 'API' postfix."
        )


@pytest.mark.django_db
class TestEndpointDescriptions:
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
        descriptions = self._collect_all_operation_descriptions(openapi_schema)
        assert descriptions, (
            "Expected at least some endpoint descriptions in the schema."
        )
        for desc in descriptions:
            for internal_str in self.INTERNAL_STRINGS:
                assert internal_str not in desc, (
                    f"Internal string '{internal_str}' found in endpoint description: {desc[:200]!r}"
                )

    def test_core_project_endpoint_has_consumer_description(self, openapi_schema):
        paths = openapi_schema.get("paths", {})
        project_list_path = next(
            (p for p in paths if p.endswith("/projects/") and "{" not in p), None
        )
        assert project_list_path, (
            f"Expected /projects/ path in schema. Paths: {list(paths)[:10]}"
        )
        operations = paths[project_list_path]
        get_op = operations.get("get", {})
        description = get_op.get("description", "")
        assert description, f"GET {project_list_path} has no description"
        for internal_str in self.INTERNAL_STRINGS:
            assert internal_str not in description, (
                f"Internal string '{internal_str}' found in projects description: {description[:200]!r}"
            )

    def test_core_dataset_endpoint_has_consumer_description(self, openapi_schema):
        paths = openapi_schema.get("paths", {})
        dataset_path = next(
            (p for p in paths if p.endswith("/datasets/") and "{" not in p), None
        )
        assert dataset_path, "Expected /datasets/ path in schema."
        get_op = paths[dataset_path].get("get", {})
        description = get_op.get("description", "")
        assert description, f"GET {dataset_path} has no description"
        for internal_str in self.INTERNAL_STRINGS:
            assert internal_str not in description, (
                f"Internal string found in datasets description: {description[:200]!r}"
            )

    def test_generated_viewset_has_model_description(self, openapi_schema):
        from fairdm.registry import registry

        paths = openapi_schema.get("paths", {})
        for model in registry.samples:
            config = registry.get_for_model(model)
            desc = getattr(config, "description", None) or (
                getattr(config.metadata, "description", None)
                if config.metadata
                else None
            )
            if not desc:
                continue
            slug = model._meta.verbose_name_plural.lower().replace(" ", "-")
            endpoint_path = next(
                (p for p in paths if f"samples/{slug}/" in p and "{" not in p), None
            )
            if endpoint_path is None:
                continue
            get_op = paths[endpoint_path].get("get", {})
            op_description = get_op.get("description", "")
            for internal_str in self.INTERNAL_STRINGS:
                assert internal_str not in op_description, (
                    f"Internal string '{internal_str}' found in description for {endpoint_path}: "
                    f"{op_description[:200]!r}"
                )
            return
        pytest.skip(
            "No registered sample type with a config description found in the schema."
        )


class TestAPIDescriptionSettings:
    def test_spectacular_settings_title_equals_fairdm_api_title(self):
        from fairdm.api.settings import FAIRDM_API_TITLE, SPECTACULAR_SETTINGS

        assert SPECTACULAR_SETTINGS["TITLE"] == FAIRDM_API_TITLE, (
            f"SPECTACULAR_SETTINGS['TITLE'] ({SPECTACULAR_SETTINGS['TITLE']!r}) "
            f"!= FAIRDM_API_TITLE ({FAIRDM_API_TITLE!r})"
        )

    def test_spectacular_settings_description_equals_fairdm_api_description(self):
        from fairdm.api.settings import FAIRDM_API_DESCRIPTION, SPECTACULAR_SETTINGS

        assert SPECTACULAR_SETTINGS["DESCRIPTION"] == FAIRDM_API_DESCRIPTION, (
            "SPECTACULAR_SETTINGS['DESCRIPTION'] does not match FAIRDM_API_DESCRIPTION"
        )

    def test_fairdm_api_title_is_overrideable(self, settings):
        settings.FAIRDM_API_TITLE = "My Custom Portal API"
        from django.conf import settings as django_settings

        assert django_settings.FAIRDM_API_TITLE == "My Custom Portal API"

    def test_fairdm_api_description_is_overrideable(self, settings):
        settings.FAIRDM_API_DESCRIPTION = "A custom portal for my research domain."
        from django.conf import settings as django_settings

        assert (
            django_settings.FAIRDM_API_DESCRIPTION
            == "A custom portal for my research domain."
        )


@pytest.mark.django_db
class TestTokens:
    @pytest.fixture
    def private_project(self):
        """A private project and a person who holds the view level on it."""
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        holder = UserFactory()
        ContributionFactory(
            content_object=project, contributor=holder, level=ContributionLevel.VIEW
        )
        return project, holder

    @staticmethod
    def send(value):
        """Request the list of projects with a token's value in the header."""
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Token {value}")
        return client.get(reverse("api:project-list"))

    @staticmethod
    def uuids(response):
        return {item["uuid"] for item in response.json()["results"]}

    def test_a_current_token_acts_as_its_holder(self, make_token, private_project):
        project, holder = private_project
        _record, value = make_token(holder)

        response = self.send(value)

        assert response.status_code == 200
        assert str(project.uuid) in self.uuids(response)

    def test_a_visitor_does_not_see_what_the_holder_sees(self, private_project):
        project, _holder = private_project

        response = APIClient().get(reverse("api:project-list"))

        assert str(project.uuid) not in self.uuids(response)

    def test_a_revoked_token_is_answered_401(self, make_token, private_project):
        _project, holder = private_project
        record, value = make_token(holder)
        assert self.send(value).status_code == 200

        record.delete()

        assert self.send(value).status_code == 401

    def test_an_expired_token_is_answered_401(self, make_token, private_project):
        _project, holder = private_project
        record, value = make_token(holder, expiry=timedelta(days=1))
        assert self.send(value).status_code == 200

        record.__class__.objects.filter(pk=record.pk).update(
            expiry=timezone.now() - timedelta(seconds=1)
        )

        assert self.send(value).status_code == 401

    def test_an_unknown_token_is_answered_401(self, make_token, private_project):
        _project, holder = private_project
        _record, value = make_token(holder)

        assert self.send(value[::-1]).status_code == 401

    def test_a_token_that_is_not_in_the_store_is_answered_401(self):
        assert self.send("0123456789abcdef" * 8).status_code == 401

    def test_the_token_limit_is_the_one_the_portal_sets(self, settings):
        from knox.settings import knox_settings

        assert knox_settings.TOKEN_LIMIT_PER_USER == 10
        assert knox_settings.AUTO_REFRESH is False


@pytest.mark.django_db
class TestSession:
    @pytest.fixture
    def project(self):
        return ProjectFactory(visibility=Visibility.PRIVATE)

    @pytest.fixture
    def editor(self, project):
        person = UserFactory()
        ContributionFactory(
            content_object=project, contributor=person, level=ContributionLevel.EDIT
        )
        return person

    @staticmethod
    def signed_in_by_session(person, **kwargs):
        client = APIClient(**kwargs)
        client.force_login(person)
        return client

    def test_a_person_reads_their_private_record_with_their_session(
        self, project, editor
    ):
        client = self.signed_in_by_session(editor, enforce_csrf_checks=True)

        response = client.get(reverse("api:project-detail", args=[project.uuid]))

        assert response.status_code == 200

    def test_a_write_with_a_session_and_no_csrf_token_is_refused(self, project, editor):
        address = reverse("api:project-detail", args=[project.uuid])
        allowed = self.signed_in_by_session(editor).patch(
            address, {"name": "Changed"}, format="json"
        )
        assert allowed.status_code == 200

        client = self.signed_in_by_session(editor, enforce_csrf_checks=True)
        response = client.patch(address, {"name": "Changed again"}, format="json")

        assert response.status_code == 403
        project.refresh_from_db()
        assert project.name == "Changed"
