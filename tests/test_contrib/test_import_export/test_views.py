"""Tests for fairdm/contrib/import_export/views.py."""

import json

import pytest
from django.urls import reverse
from django.utils import translation

from demo.models import RockSample, XRFMeasurement
from fairdm.registry import registry

pytestmark = pytest.mark.django_db


def address(model):
    """Return the Table Schema address of a registered type."""
    return reverse("table_schema", args=[model._meta.model_name])


class TestTableSchemaView:
    @pytest.mark.parametrize("model", [RockSample, XRFMeasurement])
    def test_a_visitor_downloads_a_types_schema(self, client, model):
        response = client.get(address(model))

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        assert response["Content-Disposition"] == (
            f'attachment; filename="{model._meta.model_name}-table-schema.json"'
        )

    @pytest.mark.parametrize("model", [RockSample, XRFMeasurement])
    def test_the_document_is_the_schemas_descriptor(self, client, model):
        schema = registry.get_for_model(model).get_table_schema()

        document = json.loads(client.get(address(model)).content)

        assert document == schema.as_frictionless()

    def test_the_document_holds_every_column_in_order(self, client, rock_config):
        schema = rock_config.get_table_schema()

        document = json.loads(client.get(address(RockSample)).content)

        assert [f["name"] for f in document["fields"]] == schema.headings

    def test_a_long_list_of_allowed_values_is_not_cut(self, client, rock_config):
        schema = rock_config.get_table_schema()
        longest = max(schema.columns, key=lambda column: len(column.allowed))

        document = json.loads(client.get(address(RockSample)).content)

        field = next(f for f in document["fields"] if f["name"] == longest.name)
        assert field["constraints"]["enum"] == [v for v, _ in longest.allowed]

    def test_an_unknown_type_is_not_found(self, client):
        response = client.get(reverse("table_schema", args=["nosuchtype"]))

        assert response.status_code == 404

    @pytest.mark.parametrize("language", ["en", "de"])
    def test_the_document_is_in_the_active_language(
        self, client, rock_config, language
    ):
        with translation.override(language):
            expected = rock_config.get_table_schema().as_frictionless()
            response = client.get(
                address(RockSample), headers={"accept-language": language}
            )

        assert json.loads(response.content) == expected

    def test_the_names_are_the_same_in_every_language(self, client):
        names = []
        for language in ("en", "de"):
            response = client.get(
                address(RockSample), headers={"accept-language": language}
            )
            document = json.loads(response.content)
            names.append([f["name"] for f in document["fields"]])

        assert names[0] == names[1]
