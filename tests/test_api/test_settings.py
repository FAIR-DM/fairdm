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


@pytest.fixture(scope="module")
def openapi_schema(django_db_setup, django_db_blocker):
    """The schema as the schema address serves it, generated once for the module."""
    import yaml

    with django_db_blocker.unblock():
        response = APIClient().get(
            "/api/v1/schema/", HTTP_ACCEPT="application/vnd.oai.openapi"
        )
    assert response.status_code == 200
    # drf-spectacular returns YAML by default for application/vnd.oai.openapi
    return yaml.safe_load(response.content.decode("utf-8"))


@pytest.mark.django_db
class TestSchemaComponentNaming:
    def test_no_component_name_carries_an_api_postfix(self, openapi_schema):
        components = openapi_schema.get("components", {}).get("schemas", {})
        api_named = [name for name in components if name.endswith("API")]

        assert not api_named


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


class TestAPIDescriptionSettings:
    @staticmethod
    def schema_info(client):
        """Return the ``info`` object of the schema generated now."""
        response = client.get(reverse("api:api-schema"), {"format": "json"})
        assert response.status_code == 200
        return response.json()["info"]

    def test_the_title_is_changed_through_spectacular_settings(
        self, monkeypatch, schema_client
    ):
        from drf_spectacular.settings import spectacular_settings

        monkeypatch.setattr(spectacular_settings, "TITLE", "My Custom Portal API")

        assert self.schema_info(schema_client)["title"] == "My Custom Portal API"


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


@pytest.mark.django_db
class TestOtherOrigins:
    ORIGIN = "https://another-site.example"

    def test_a_response_to_another_origin_may_be_read_by_it(self):
        response = APIClient().get(reverse("api:project-list"), HTTP_ORIGIN=self.ORIGIN)

        assert response["Access-Control-Allow-Origin"] in ("*", self.ORIGIN)

    def test_the_authorization_header_is_allowed_in_a_preflight(self):
        response = APIClient().options(
            reverse("api:project-list"),
            HTTP_ORIGIN=self.ORIGIN,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS="authorization",
        )

        allowed = response["Access-Control-Allow-Headers"].lower().split(", ")
        assert response.status_code == 200
        assert "authorization" in allowed

    @pytest.mark.parametrize("method", ["get", "options"])
    def test_no_response_permits_credentials(self, method):
        response = getattr(APIClient(), method)(
            reverse("api:project-list"),
            HTTP_ORIGIN=self.ORIGIN,
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        assert "Access-Control-Allow-Credentials" not in response

    def test_a_page_outside_the_api_gets_no_cors_header(self):
        response = APIClient().get(reverse("home"), HTTP_ORIGIN=self.ORIGIN)

        assert "Access-Control-Allow-Origin" not in response
