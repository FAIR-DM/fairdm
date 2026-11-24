"""Tests for fairdm/contrib/import_export/schema.py."""

import csv

import frictionless
import pytest
from controlled_vocabularies.models import Record
from django.db import connection, models
from django.test.utils import CaptureQueriesContext
from django.utils import translation

from demo.factories import RockSampleFactory
from demo.models import (
    CustomSample,
    ExampleMeasurement,
    ICP_MS_Measurement,
    RockSample,
)
from fairdm.contrib.import_export.schema import (
    Column,
    TableSchema,
    build_table_schema,
    kind_of,
)
from fairdm.contrib.import_export.widgets import render_cell
from fairdm.core.models import Measurement, Sample
from fairdm.factories import DatasetFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from fairdm.utils.location.resources import LOCATION_COLUMNS

pytestmark = pytest.mark.django_db

ROCK_OWN = [
    "rock_type",
    "mineral_content",
    "weight_grams",
    "collection_date",
    "hardness_mohs",
]
XRF_OWN = [
    "element",
    "concentration_ppm",
    "detection_limit_ppm",
    "instrument_model",
    "measurement_conditions",
]


def headings(config):
    """Return the headings of a configuration's table schema, in order."""
    return build_table_schema(config).headings


class TestColumnOrder:
    def test_sample_without_resource_fields(self, rock_config):
        assert headings(rock_config) == [
            "portal_id",
            "local_id",
            "name",
            *ROCK_OWN,
            "status",
            *LOCATION_COLUMNS,
        ]

    def test_measurement_has_its_sample_after_the_name_and_no_status(self, xrf_config):
        assert headings(xrf_config) == [
            "portal_id",
            "local_id",
            "name",
            "sample",
            "sample_name",
            *XRF_OWN,
            *LOCATION_COLUMNS,
        ]

    def test_sample_name_is_written_on_export_only(self, xrf_config):
        schema = build_table_schema(xrf_config)
        assert schema.get("sample_name").role == "export"
        assert schema.get("sample_name").importable is False
        assert schema.get("sample").role == "field"
        assert schema.get("sample").required is True

    def test_identifiers_carry_their_roles(self, rock_config):
        schema = build_table_schema(rock_config)
        assert schema.get("portal_id").role == "key"
        assert schema.get("local_id").role == "match"
        assert schema.get("name").role == "field"

    def test_groups_run_identifiers_own_shared(self, rock_config):
        schema = build_table_schema(rock_config)
        assert [key for key, *rest in schema.groups()] == [
            "ids",
            "own",
            "shared",
        ]

    @pytest.mark.parametrize("config_name", ["rock_config", "xrf_config"])
    def test_the_shared_heading_is_one_whole_translatable_string(
        self, request, monkeypatch, config_name
    ):
        from fairdm.contrib.import_export import schema as schema_module

        asked = []

        def record(message):
            asked.append(message)
            return message

        monkeypatch.setattr(schema_module, "_", record)
        schema = build_table_schema(request.getfixturevalue(config_name))

        titles = {key: title for key, title, columns in schema.groups()}

        assert titles["shared"] in asked

    def test_schema_describes_its_model(self, rock_config):
        schema = build_table_schema(rock_config)
        assert isinstance(schema, TableSchema)
        assert schema.model is RockSample
        assert schema.kind == "sample"
        assert schema.slug == "rocksample"


class TestResourceFieldsRule:
    def test_listed_fields_and_required_fields_are_columns(self, rock_config_for):
        config = rock_config_for(resource_fields=["weight_grams"])
        assert headings(config) == [
            "portal_id",
            "local_id",
            "name",
            "rock_type",
            "weight_grams",
            "collection_date",
        ]

    def test_status_only_when_named(self, rock_config_for):
        config = rock_config_for(resource_fields=["weight_grams", "status"])
        assert "status" in headings(config)
        assert not set(LOCATION_COLUMNS) & set(headings(config))

    def test_grouped_names_count_as_listed(self, rock_config_for):
        config = rock_config_for(resource_fields=[("weight_grams", "hardness_mohs")])
        assert {"weight_grams", "hardness_mohs"} <= set(headings(config))

    def test_location_names_all_four_columns(self, rock_config_for):
        config = rock_config_for(resource_fields=["location"])
        columns = headings(config)
        assert columns[-4:] == list(LOCATION_COLUMNS)
        assert "status" not in columns

    def test_unlisted_optional_fields_are_left_out(self, rock_config_for):
        config = rock_config_for(resource_fields=["weight_grams"])
        assert "mineral_content" not in headings(config)
        assert "hardness_mohs" not in headings(config)

    def test_exclude_drops_an_optional_field(self, rock_config_for):
        config = rock_config_for(exclude=["weight_grams"])
        assert "weight_grams" not in headings(config)
        assert "mineral_content" in headings(config)

    def test_exclude_keeps_a_field_a_record_cannot_be_saved_without(
        self, rock_config_for
    ):
        config = rock_config_for(exclude=["rock_type", "weight_grams"])
        assert "rock_type" in headings(config)
        assert "weight_grams" not in headings(config)

    def test_exclude_does_not_drop_the_identifiers(self, rock_config_for):
        config = rock_config_for(exclude=["name", "local_id"])
        assert headings(config)[:3] == ["portal_id", "local_id", "name"]


class TestColumnContents:
    @pytest.mark.parametrize(
        "name",
        [
            "uuid",
            "id",
            "added",
            "modified",
            "image",
            "options",
            "dataset",
            "keywords",
            "tags",
            "location",
            "polymorphic_ctype",
            "sample_ptr",
        ],
    )
    def test_fields_the_portal_sets_are_never_columns(self, rock_config, name):
        assert name not in headings(rock_config)

    def test_a_field_that_is_not_editable_is_never_a_column(self, rock_config):
        for model_field in RockSample._meta.concrete_fields:
            if not model_field.editable or getattr(model_field, "auto_now", False):
                assert model_field.name not in headings(rock_config)

    @pytest.mark.parametrize("language", ["en", "de"])
    def test_headings_are_the_field_names_in_every_language(
        self, rock_config, language
    ):
        with translation.override(language):
            columns = headings(rock_config)
        assert columns == headings(rock_config)
        own = [c for c in columns if c in ROCK_OWN]
        assert own == ROCK_OWN

    def test_a_unit_in_brackets_becomes_the_unit_and_a_bare_alias(self, rock_config):
        column = build_table_schema(rock_config).get("weight_grams")
        assert column.unit == "grams"
        assert column.label == "Weight (grams)"
        assert "Weight" in column.aliases

    def test_a_quantity_column_has_the_fields_base_unit(self, icp_config):
        column = build_table_schema(icp_config).get("value")
        base_units = ICP_MS_Measurement._meta.get_field("value").base_units
        assert column.kind == "quantity"
        assert column.unit == str(base_units)

    @pytest.mark.parametrize(
        ("name", "kind"),
        [
            ("portal_id", "id"),
            ("rock_type", "text"),
            ("weight_grams", "number"),
            ("collection_date", "date"),
            ("hardness_mohs", "number"),
            ("status", "concept"),
            ("latitude", "latitude"),
            ("longitude", "longitude"),
        ],
    )
    def test_kinds(self, rock_config, name, kind):
        assert build_table_schema(rock_config).get(name).kind == kind

    def test_required_follows_the_model_field(self, rock_config):
        schema = build_table_schema(rock_config)
        assert schema.get("rock_type").required is True
        assert schema.get("collection_date").required is True
        assert schema.get("mineral_content").required is False
        assert schema.get("weight_grams").required is False
        assert schema.get("status").required is False
        assert schema.get("local_id").required is False

    def test_constraints_come_from_the_model_field(self, rock_config):
        schema = build_table_schema(rock_config)
        assert schema.get("rock_type").max_length == 100
        assert schema.get("hardness_mohs").decimals == 1

    def test_the_description_is_the_fields_help_text(self, rock_config):
        column = build_table_schema(rock_config).get("rock_type")
        assert str(column.description) == str(
            RockSample._meta.get_field("rock_type").help_text
        )

    def test_a_concept_column_lists_every_preferred_label(self, rock_config):
        status = Sample._meta.get_field("status")
        expected = set(
            Record.objects.filter(status.resolve_restriction()).values_list(
                "pref_label", flat=True
            )
        )
        column = build_table_schema(rock_config).get("status")
        assert expected
        assert {value for value, meaning in column.allowed} == expected
        assert len(column.allowed) == len(expected)

    def test_a_concept_columns_values_do_not_change_with_language(self, rock_config):
        with translation.override("en"):
            english = build_table_schema(rock_config).get("status").allowed
        with translation.override("de"):
            german = build_table_schema(rock_config).get("status").allowed
        assert english == german

    def test_headings_are_unique(self, rock_config):
        columns = headings(rock_config)
        assert len(columns) == len(set(columns))


class TestKindOf:
    @pytest.mark.parametrize(
        ("model_field", "kind"),
        [
            (models.CharField(max_length=10), "text"),
            (models.TextField(), "text"),
            (models.BooleanField(), "boolean"),
            (models.IntegerField(), "integer"),
            (models.PositiveSmallIntegerField(), "integer"),
            (models.FloatField(), "number"),
            (models.DecimalField(max_digits=5, decimal_places=2), "number"),
            (models.DateField(), "date"),
            (models.DateTimeField(), "datetime"),
            (models.TimeField(), "time"),
            (models.CharField(max_length=5, choices=[("a", "A")]), "choice"),
        ],
    )
    def test_kind(self, model_field, kind):
        assert kind_of(model_field) == kind


class TestExamples:
    def test_every_column_has_an_example(self, rock_config):
        for column in build_table_schema(rock_config).columns:
            if column.role != "export":
                assert column.example, column.name

    def test_a_list_column_is_exampled_by_its_first_value(self, rock_config):
        column = build_table_schema(rock_config).get("status")
        assert column.example == column.allowed[0][0]

    def test_an_example_lies_inside_the_columns_range(self, rock_config):
        schema = build_table_schema(rock_config)
        for name in ("latitude", "longitude", "location_uncertainty"):
            column = schema.get(name)
            value = float(column.example)
            if column.minimum is not None:
                assert value >= column.minimum
            if column.maximum is not None:
                assert value <= column.maximum

    def test_a_decimal_example_fits_the_decimal_places(self, rock_config):
        column = build_table_schema(rock_config).get("hardness_mohs")
        assert len(column.example.partition(".")[2]) <= column.decimals

    def test_a_private_record_never_reaches_an_example(self, rock_config):
        private = DatasetFactory(visibility=Visibility.PRIVATE)
        before = [c.example for c in build_table_schema(rock_config).columns]
        RockSampleFactory(
            dataset=private,
            name="SECRET-NAME",
            local_id="SECRET-LOCAL",
            rock_type="SECRET-ROCK",
            mineral_content="SECRET-MINERALS",
        )
        after = [c.example for c in build_table_schema(rock_config).columns]
        assert after == before
        assert not any("SECRET" in example for example in after)

    def test_building_never_queries_the_types_own_table(self, rock_config):
        RockSampleFactory()
        with CaptureQueriesContext(connection) as queries:
            build_table_schema(rock_config)
        tables = [RockSample._meta.db_table, Sample._meta.db_table]
        for query in queries.captured_queries:
            for table in tables:
                assert f'"{table}"' not in query["sql"]


class TestLocationColumns:
    def test_sample_columns_are_named_by_the_shared_constant(self, rock_config):
        columns = headings(rock_config)
        assert tuple(columns[-4:]) == LOCATION_COLUMNS

    def test_measurement_columns_are_named_by_the_shared_constant(self, xrf_config):
        columns = headings(xrf_config)
        assert tuple(columns[-4:]) == LOCATION_COLUMNS

    def test_bounds_and_units(self, rock_config):
        schema = build_table_schema(rock_config)
        assert (schema.get("latitude").minimum, schema.get("latitude").maximum) == (
            -90,
            90,
        )
        assert (schema.get("longitude").minimum, schema.get("longitude").maximum) == (
            -180,
            180,
        )
        assert schema.get("location_elevation").unit == "m"
        assert schema.get("location_uncertainty").unit == "m"
        assert schema.get("location_uncertainty").minimum == 0

    @pytest.mark.parametrize("name", ["location_elevation", "location_uncertainty"])
    def test_naming_one_extra_column_brings_the_coordinates_it_needs(
        self, rock_config_for, name
    ):
        columns = headings(rock_config_for(resource_fields=[name]))
        assert columns[-3:] == ["latitude", "longitude", name]
        assert "location_uncertainty" not in columns or name == "location_uncertainty"

    def test_the_columns_are_in_the_shared_group(self, rock_config):
        schema = build_table_schema(rock_config)
        assert {schema.get(name).group for name in LOCATION_COLUMNS} == {"shared"}

    def test_a_column_is_a_column(self, rock_config):
        assert isinstance(build_table_schema(rock_config).get("latitude"), Column)


@pytest.mark.parametrize(
    "model", [*registry.samples, *registry.measurements], ids=lambda m: m.__name__
)
class TestPortalConfig:
    def test_a_registered_type_has_a_schema_with_no_further_work(self, model):
        config = registry.get_for_model(model)
        schema = config.get_table_schema()
        assert schema.model is model
        assert schema.headings[:3] == ["portal_id", "local_id", "name"]
        assert len(schema.headings) == len(set(schema.headings))
        assert all(isinstance(column, Column) for column in schema.columns)

    def test_every_column_belongs_to_a_group(self, model):
        schema = registry.get_for_model(model).get_table_schema()
        assert {column.group for column in schema.columns} <= {"ids", "own", "shared"}


TYPES = [*registry.samples, *registry.measurements]
RANGED = [m for m in TYPES if m is not CustomSample]
LISTED = [m for m in registry.samples if m is not CustomSample]


def write_file(path, schema, rows):
    """Write a CSV file of rows under the schema's headings and return its path."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(schema.headings)
        writer.writerows(rows)
    return path


def valid(path, schema):
    """Say whether the standard validator accepts the file under the schema."""
    resource = frictionless.Resource(
        path=path.name,
        basepath=str(path.parent),
        schema=frictionless.Schema.from_descriptor(schema.as_frictionless()),
    )
    return frictionless.validate(resource).valid


@pytest.fixture
def exported(factory_for, tmp_path):
    """Return a function writing the file an export of built records of a type holds."""

    def build(model, count=2):
        """Write the export.

        Args:
            model: The registered sample or measurement model.
            count: How many records to build.

        Returns:
            The schema, the rows and the path of the file.
        """
        schema = registry.get_for_model(model).get_table_schema()
        extra = (
            {"sample": RockSampleFactory()} if issubclass(model, Measurement) else {}
        )
        records = [factory_for(model)(**extra) for _ in range(count)]
        rows = [[render_cell(c, record) for c in schema.columns] for record in records]
        return schema, rows, write_file(tmp_path / "export.csv", schema, rows)

    return build


@pytest.mark.parametrize("model", TYPES, ids=lambda m: m.__name__)
class TestFrictionlessValidation:
    def test_the_descriptor_is_a_valid_schema(self, model):
        schema = registry.get_for_model(model).get_table_schema()

        descriptor = frictionless.Schema.from_descriptor(schema.as_frictionless())

        assert [f.name for f in descriptor.fields] == schema.headings

    def test_a_file_an_export_wrote_validates(self, model, exported):
        schema, _rows, path = exported(model)

        assert valid(path, schema)

    def test_a_file_of_new_records_with_no_portal_id_validates(
        self, model, exported, tmp_path
    ):
        schema, rows, _path = exported(model)
        index = schema.headings.index("portal_id")
        fresh = [[*row[:index], "", *row[index + 1 :]] for row in rows]

        assert valid(write_file(tmp_path / "new.csv", schema, fresh), schema)

    def test_a_file_with_the_same_portal_id_twice_fails(
        self, model, exported, tmp_path
    ):
        schema, rows, _path = exported(model)
        index = schema.headings.index("portal_id")
        rows[1][index] = rows[0][index]

        assert not valid(write_file(tmp_path / "twice.csv", schema, rows), schema)

    def test_the_schema_has_no_primary_key_and_the_portal_id_is_unique(self, model):
        schema = registry.get_for_model(model).get_table_schema()

        descriptor = schema.as_frictionless()

        assert "primaryKey" not in descriptor
        portal_id = descriptor["fields"][0]
        assert portal_id["name"] == "portal_id"
        assert portal_id["constraints"]["unique"] is True
        assert "required" not in portal_id["constraints"]

    def test_the_missing_value_is_the_empty_cell(self, model):
        schema = registry.get_for_model(model).get_table_schema()

        assert schema.as_frictionless()["missingValues"] == [""]


class TestFrictionlessRefusals:
    @pytest.mark.parametrize("model", RANGED, ids=lambda m: m.__name__)
    def test_a_cell_outside_a_range_fails(self, model, exported, tmp_path):
        schema, rows, _path = exported(model)
        column = next(c for c in schema.columns if c.maximum is not None)
        rows[0][schema.headings.index(column.name)] = str(column.maximum + 1)

        assert not valid(write_file(tmp_path / "range.csv", schema, rows), schema)

    @pytest.mark.parametrize("model", LISTED, ids=lambda m: m.__name__)
    def test_a_value_not_in_the_list_fails(self, model, exported, tmp_path):
        schema, rows, _path = exported(model)
        column = next(c for c in schema.columns if c.allowed)
        rows[0][schema.headings.index(column.name)] = "not-in-the-list"

        assert not valid(write_file(tmp_path / "listed.csv", schema, rows), schema)


class TestFrictionlessDescriptor:
    def field(self, schema, name):
        """Return the descriptor of one column."""
        return next(f for f in schema.as_frictionless()["fields"] if f["name"] == name)

    def test_a_list_names_every_allowed_value(self, rock_config):
        schema = rock_config.get_table_schema()
        column = schema.get("status")

        field = self.field(schema, "status")

        assert field["constraints"]["enum"] == [v for v, _meaning in column.allowed]

    @pytest.mark.parametrize(
        ("model", "name", "kind"),
        [
            (RockSample, "collection_date", "date"),
            (ICP_MS_Measurement, "analysis_date", "datetime"),
        ],
    )
    def test_a_date_or_datetime_has_the_default_format(self, model, name, kind):
        schema = registry.get_for_model(model).get_table_schema()

        field = self.field(schema, name)

        assert field["type"] == kind
        assert field["format"] == "default"

    def test_a_time_has_the_default_format(self):
        schema = registry.get_for_model(ExampleMeasurement).get_table_schema()

        field = self.field(schema, "time_field")

        assert field["type"] == "time"
        assert field["format"] == "default"

    def test_a_boolean_reads_yes_and_no(self):
        schema = registry.get_for_model(CustomSample).get_table_schema()

        field = self.field(schema, "boolean_field")

        assert field["type"] == "boolean"
        assert field["trueValues"] == ["yes"]
        assert field["falseValues"] == ["no"]

    def test_a_partial_date_is_a_pattern(self, make_column):
        schema = TableSchema(
            model=RockSample, config=None, columns=[make_column("partial_date")]
        )

        field = schema.as_frictionless()["fields"][0]

        assert field["type"] == "string"
        assert field["constraints"]["pattern"] == r"^\d{4}(-\d{2}(-\d{2})?)?$"

    def test_the_export_only_column_is_not_read_on_import(self, xrf_config):
        schema = xrf_config.get_table_schema()

        assert self.field(schema, "sample_name")["readOnImport"] is False
        assert "readOnImport" not in self.field(schema, "sample")

    def test_a_unit_is_a_custom_property(self, rock_config):
        field = self.field(rock_config.get_table_schema(), "weight_grams")

        assert field["unit"] == "grams"
