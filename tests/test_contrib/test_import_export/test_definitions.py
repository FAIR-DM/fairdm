"""Tests for fairdm/contrib/import_export/definitions.py."""

import pytest
from django.contrib.auth import get_user_model
from import_export.formats.base_formats import CSV, XLSX

from demo.models import RockSample, XRFMeasurement
from fairdm.contrib.import_export.definitions import (
    ImportDefinition,
    ImportDefinitions,
    import_definitions,
)
from fairdm.registry import registry


class TestLookup:
    """FR-011 and FR-012: one definition per registered type."""

    def test_one_definition_per_registered_type(self):
        names = [definition.name for definition in import_definitions.all()]

        expected = [
            model._meta.model_name
            for model in [*registry.samples, *registry.measurements]
        ]
        assert sorted(names) == sorted(expected)

    @pytest.mark.parametrize("model", [RockSample, XRFMeasurement])
    def test_kind_follows_the_model(self, model):
        definition = import_definitions.get(model._meta.model_name)

        expected = "sample" if model in registry.samples else "measurement"
        assert definition.model is model
        assert definition.kind == expected

    def test_formats_are_the_import_formats_setting(self, settings):
        settings.IMPORT_FORMATS = [CSV, XLSX]

        definition = import_definitions.get("rocksample")

        assert definition.formats == ("csv", "xlsx")

    def test_formats_follow_the_setting_at_call_time(self, settings):
        settings.IMPORT_FORMATS = [CSV]
        first = import_definitions.get("rocksample").formats
        settings.IMPORT_FORMATS = [XLSX]

        assert import_definitions.get("rocksample").formats != first

    @pytest.mark.django_db
    def test_table_schema_is_the_configurations(self):
        definition = import_definitions.get("rocksample")

        expected = registry.get_for_model(RockSample).get_table_schema()
        assert definition.table_schema().columns == expected.columns

    def test_unknown_name_is_none(self):
        assert import_definitions.get("no-such-type") is None

    def test_definitions_filter_by_kind(self):
        samples = import_definitions.all(kind="sample")
        measurements = import_definitions.all(kind="measurement")

        assert samples
        assert measurements
        assert {d.kind for d in samples} == {"sample"}
        assert {d.kind for d in measurements} == {"measurement"}
        assert len(samples) + len(measurements) == len(import_definitions.all())


class TestRegister:
    """FR-013: a project adds its own definition."""

    def test_added_definition_is_found_and_listed(self, added_definitions):
        own = ImportDefinition(name="rocks-by-hand", model=RockSample, formats=("csv",))

        import_definitions.register(own)

        assert import_definitions.get("rocks-by-hand") == own
        assert own in import_definitions.all()

    def test_added_definition_is_filed_by_kind(self, added_definitions):
        own = ImportDefinition(name="rocks-by-hand", model=RockSample, formats=("csv",))

        import_definitions.register(own)

        assert own in import_definitions.all(kind="sample")
        assert own not in import_definitions.all(kind="measurement")

    def test_built_in_name_is_refused(self, added_definitions):
        own = ImportDefinition(name="rocksample", model=RockSample, formats=("csv",))

        with pytest.raises(ValueError):
            import_definitions.register(own)

    def test_added_name_is_refused_a_second_time(self, added_definitions):
        own = ImportDefinition(name="rocks-by-hand", model=RockSample, formats=("csv",))
        import_definitions.register(own)

        with pytest.raises(ValueError):
            import_definitions.register(own)

    def test_unregistered_model_is_refused(self, added_definitions):
        own = ImportDefinition(name="users", model=get_user_model(), formats=("csv",))

        with pytest.raises(ValueError):
            import_definitions.register(own)

        assert import_definitions.get("users") is None


class TestImportDefinitions:
    """FR-013: the definitions are one object a portal can subclass."""

    def test_a_collection_keeps_what_it_adds_to_itself(self):
        own = ImportDefinition(name="rocks-by-hand", model=RockSample, formats=("csv",))
        collection = ImportDefinitions()

        collection.register(own)

        assert collection.get("rocks-by-hand") == own
        assert import_definitions.get("rocks-by-hand") is None
