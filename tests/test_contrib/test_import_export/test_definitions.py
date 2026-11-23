"""Tests for fairdm/contrib/import_export/definitions.py."""

import pytest
from django.contrib.auth import get_user_model
from import_export.formats.base_formats import CSV, XLSX

from demo.models import RockSample
from fairdm.contrib.import_export.definitions import (
    ImportDefinition,
    definitions,
    get_definition,
    register,
)
from fairdm.registry import registry

pytestmark = pytest.mark.django_db


class TestLookup:
    """FR-011 and FR-012: one definition per registered type."""

    def test_one_definition_per_registered_type(self):
        names = [definition.name for definition in definitions()]

        expected = [
            model._meta.model_name
            for model in [*registry.samples, *registry.measurements]
        ]
        assert names == expected

    @pytest.mark.parametrize("model", [*registry.samples, *registry.measurements])
    def test_kind_follows_the_model(self, model):
        definition = get_definition(model._meta.model_name)

        expected = "sample" if model in registry.samples else "measurement"
        assert definition.model is model
        assert definition.kind == expected

    def test_formats_are_the_import_formats_setting(self, settings):
        settings.IMPORT_FORMATS = [CSV, XLSX]

        definition = get_definition("rocksample")

        assert definition.formats == ("csv", "xlsx")

    def test_formats_follow_the_setting_at_call_time(self, settings):
        settings.IMPORT_FORMATS = [CSV]
        first = get_definition("rocksample").formats
        settings.IMPORT_FORMATS = [XLSX]

        assert get_definition("rocksample").formats != first

    def test_table_schema_is_the_configurations(self):
        definition = get_definition("rocksample")

        expected = registry.get_for_model(RockSample).get_table_schema()
        assert definition.table_schema().columns == expected.columns

    def test_unknown_name_is_none(self):
        assert get_definition("no-such-type") is None

    def test_definitions_filter_by_kind(self):
        samples = definitions(kind="sample")
        measurements = definitions(kind="measurement")

        assert samples
        assert measurements
        assert {d.kind for d in samples} == {"sample"}
        assert {d.kind for d in measurements} == {"measurement"}
        assert len(samples) + len(measurements) == len(definitions())


class TestRegister:
    """FR-013: a project adds its own definition."""

    def test_added_definition_is_found_and_listed(self, added_definitions):
        own = ImportDefinition(name="rocks-by-hand", model=RockSample, formats=("csv",))

        register(own)

        assert get_definition("rocks-by-hand") == own
        assert own in definitions()

    def test_added_definition_is_filed_by_kind(self, added_definitions):
        own = ImportDefinition(name="rocks-by-hand", model=RockSample, formats=("csv",))

        register(own)

        assert own in definitions(kind="sample")
        assert own not in definitions(kind="measurement")

    def test_built_in_name_is_refused(self, added_definitions):
        own = ImportDefinition(name="rocksample", model=RockSample, formats=("csv",))

        with pytest.raises(ValueError):
            register(own)

    def test_added_name_is_refused_a_second_time(self, added_definitions):
        own = ImportDefinition(name="rocks-by-hand", model=RockSample, formats=("csv",))
        register(own)

        with pytest.raises(ValueError):
            register(own)

    def test_unregistered_model_is_refused(self, added_definitions):
        own = ImportDefinition(name="users", model=get_user_model(), formats=("csv",))

        with pytest.raises(ValueError):
            register(own)

        assert get_definition("users") is None
