"""Tests for fairdm/contrib/import_export/resources.py."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from import_export.results import RowResult

from demo.factories import RockSampleFactory, SoilSampleFactory
from demo.models import RockSample, XRFMeasurement
from fairdm.contrib.import_export.definitions import get_definition
from fairdm.contrib.import_export.resources import (
    RowProblem,
    build_resource,
    changed_cells,
)
from fairdm.core.measurement.models import Measurement
from fairdm.factories import DatasetFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db

NEW = RowResult.IMPORT_TYPE_NEW
UPDATE = RowResult.IMPORT_TYPE_UPDATE
SKIP = RowResult.IMPORT_TYPE_SKIP
INVALID = RowResult.IMPORT_TYPE_INVALID
ERROR = RowResult.IMPORT_TYPE_ERROR


def rock_row(**overrides):
    """Return the cells of a new rock with every required column filled."""
    row = {
        "name": "Granite",
        "rock_type": "granite",
        "collection_date": "2024-06-30",
    }
    row.update(overrides)
    return row


def outcomes(result):
    """Return the import type of each row of a result."""
    return [row.import_type for row in result.rows]


def problem_of(result, index=0):
    """Return the RowProblem a row of a result ended in."""
    error = result.rows[index].errors[0].error
    assert isinstance(error, RowProblem)
    return error


class TestRecordLookup:
    """A row finds its record by portal ID, then by Local ID within the dataset."""

    @pytest.fixture
    def rock(self, open_dataset):
        """A stored rock with a Local ID."""
        return RockSampleFactory(
            dataset=open_dataset, local_id="R-1", rock_type="granite"
        )

    def test_a_portal_id_finds_the_record(self, run_import, rock):
        _, result = run_import(
            RockSample, [{"portal_id": rock.uuid, "rock_type": "basalt"}]
        )

        rock.refresh_from_db()
        assert (outcomes(result), rock.rock_type) == ([UPDATE], "basalt")

    def test_a_local_id_finds_the_record_when_there_is_no_portal_id(
        self, run_import, rock
    ):
        _, result = run_import(RockSample, [{"local_id": "R-1", "rock_type": "basalt"}])

        rock.refresh_from_db()
        assert (outcomes(result), rock.rock_type) == ([UPDATE], "basalt")

    def test_the_portal_id_decides_when_the_local_id_names_another_record(
        self, run_import, open_dataset, rock
    ):
        other = RockSampleFactory(dataset=open_dataset, local_id="R-2")

        _, result = run_import(
            RockSample,
            [{"portal_id": rock.uuid, "local_id": "R-2", "rock_type": "basalt"}],
        )

        rock.refresh_from_db()
        other.refresh_from_db()
        assert (outcomes(result), rock.rock_type, other.rock_type) == (
            [UPDATE],
            "basalt",
            other.rock_type,
        )
        assert rock.local_id == "R-2"

    def test_a_local_id_of_another_dataset_finds_nothing(self, run_import, rock):
        elsewhere = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        _, result = run_import(
            RockSample, [rock_row(local_id="R-1")], dataset=elsewhere
        )

        assert outcomes(result) == [NEW]
        assert RockSample.objects.filter(local_id="R-1").count() == 2

    def test_a_name_never_finds_a_record(self, run_import, open_dataset):
        RockSampleFactory(dataset=open_dataset, name="Granite")

        _, result = run_import(RockSample, [rock_row(name="Granite")])

        assert outcomes(result) == [NEW]

    def test_a_portal_id_nobody_holds_is_a_row_problem(self, run_import):
        _, result = run_import(RockSample, [rock_row(portal_id="sNOBODYHOLDSTHIS")])

        assert (outcomes(result), problem_of(result).column) == ([ERROR], "portal_id")

    def test_a_portal_id_of_another_type_is_a_row_problem(
        self, run_import, open_dataset
    ):
        soil = SoilSampleFactory(dataset=open_dataset)

        _, result = run_import(RockSample, [rock_row(portal_id=soil.uuid)])

        assert (outcomes(result), problem_of(result).column) == ([ERROR], "portal_id")
        assert not RockSample.objects.filter(name="Granite").exists()

    def test_a_local_id_held_by_two_records_is_a_row_problem(
        self, run_import, open_dataset, rock
    ):
        RockSampleFactory(dataset=open_dataset, local_id="R-1")

        _, result = run_import(RockSample, [{"local_id": "R-1", "rock_type": "x"}])

        assert (outcomes(result), problem_of(result).column) == ([ERROR], "local_id")

    def test_a_portal_id_of_another_dataset_is_left_out_with_a_note(self, run_import):
        elsewhere = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True),
            rock_type="granite",
        )

        resource, result = run_import(
            RockSample, [{"portal_id": elsewhere.uuid, "rock_type": "basalt"}]
        )

        elsewhere.refresh_from_db()
        assert (outcomes(result), elsewhere.rock_type) == ([SKIP], "granite")
        assert resource.notes[1]

    def test_the_note_on_a_measurement_of_another_dataset_points_at_the_sample_column(
        self, run_import, make_record
    ):
        elsewhere = make_record(
            XRFMeasurement,
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True),
        )
        sample_resource, _ = run_import(
            RockSample, [{"portal_id": RockSampleFactory().uuid}]
        )

        resource, result = run_import(
            XRFMeasurement, [{"portal_id": elsewhere.uuid, "element": "Fe"}]
        )

        assert outcomes(result) == [SKIP]
        assert resource.notes[1] != sample_resource.notes[1]

    def test_the_resolved_record_of_each_row_is_kept_for_duplicate_detection(
        self, run_import, rock
    ):
        resource, _ = run_import(
            RockSample,
            [
                {"portal_id": rock.uuid, "rock_type": "basalt"},
                {"local_id": "R-1", "rock_type": "gabbro"},
                rock_row(name="Fresh"),
            ],
        )

        assert resource.record_pks[1] == resource.record_pks[2] == rock.pk
        assert 3 not in resource.record_pks


class TestModes:
    """The mode says which rows are written and which are left out with a reason."""

    @pytest.fixture
    def rock(self, open_dataset):
        """A stored rock with a Local ID."""
        return RockSampleFactory(
            dataset=open_dataset, local_id="R-1", rock_type="granite"
        )

    @pytest.fixture
    def both_rows(self, rock):
        """A row for the stored rock and a row for a new one."""
        return [
            {"local_id": "R-1", "rock_type": "basalt"},
            rock_row(local_id="R-9"),
        ]

    def test_both_adds_and_changes(self, run_import, rock, both_rows):
        _, result = run_import(RockSample, both_rows, mode="both")

        rock.refresh_from_db()
        assert (outcomes(result), rock.rock_type) == ([UPDATE, NEW], "basalt")

    def test_add_leaves_out_a_row_that_matches_a_record(
        self, run_import, rock, both_rows
    ):
        resource, result = run_import(RockSample, both_rows, mode="add")

        rock.refresh_from_db()
        assert (outcomes(result), rock.rock_type) == ([SKIP, NEW], "granite")
        assert resource.notes[1]
        assert 2 not in resource.notes

    def test_update_leaves_out_a_row_that_matches_nothing(
        self, run_import, rock, both_rows
    ):
        resource, result = run_import(RockSample, both_rows, mode="update")

        assert outcomes(result) == [UPDATE, SKIP]
        assert resource.notes[2]
        assert not RockSample.objects.filter(local_id="R-9").exists()

    def test_a_row_that_changes_nothing_is_left_out_without_a_note(
        self, run_import, rock
    ):
        resource, result = run_import(
            RockSample, [{"local_id": "R-1", "rock_type": "granite"}]
        )

        assert outcomes(result) == [SKIP]
        assert 1 not in resource.notes


class TestEmptyCells:
    """An empty cell keeps the stored value unless the person asked for it cleared."""

    @pytest.fixture
    def rock(self, open_dataset):
        """A stored rock with optional values."""
        return RockSampleFactory(
            dataset=open_dataset,
            local_id="R-1",
            mineral_content="quartz",
            weight_grams=12.5,
        )

    def test_keep_leaves_the_stored_value(self, run_import, rock):
        _, result = run_import(
            RockSample,
            [{"local_id": "R-1", "mineral_content": "", "weight_grams": ""}],
            empty="keep",
        )

        rock.refresh_from_db()
        assert outcomes(result) == [SKIP]
        assert (rock.mineral_content, rock.weight_grams) == ("quartz", 12.5)

    def test_clear_empties_the_stored_value(self, run_import, rock):
        _, result = run_import(
            RockSample,
            [{"local_id": "R-1", "mineral_content": "", "weight_grams": ""}],
            empty="clear",
        )

        rock.refresh_from_db()
        assert outcomes(result) == [UPDATE]
        assert (rock.mineral_content, rock.weight_grams) == ("", None)

    def test_an_empty_optional_cell_on_a_new_row_leaves_the_default(self, run_import):
        _, result = run_import(
            RockSample, [rock_row(mineral_content="", weight_grams="")]
        )

        record = RockSample.objects.get(name="Granite")
        assert (outcomes(result), record.weight_grams) == ([NEW], None)


class TestFieldProblems:
    """Every problem of a row is reported, and a row with a problem writes nothing."""

    @pytest.fixture
    def rock(self, open_dataset):
        """A stored rock."""
        return RockSampleFactory(
            dataset=open_dataset, local_id="R-1", rock_type="granite"
        )

    def test_an_empty_cell_in_a_required_column_of_a_new_row_is_a_problem(
        self, run_import
    ):
        _, result = run_import(RockSample, [rock_row(rock_type="")])

        assert (outcomes(result), problem_of(result).column) == ([ERROR], "rock_type")
        assert not RockSample.objects.filter(name="Granite").exists()

    def test_clearing_a_required_value_on_an_update_is_a_problem(
        self, run_import, rock
    ):
        _, result = run_import(
            RockSample, [{"local_id": "R-1", "rock_type": ""}], empty="clear"
        )

        rock.refresh_from_db()
        assert (outcomes(result), problem_of(result).column) == ([ERROR], "rock_type")
        assert rock.rock_type == "granite"

    def test_an_empty_required_cell_is_kept_when_empty_cells_are_kept(
        self, run_import, rock
    ):
        _, result = run_import(
            RockSample, [{"local_id": "R-1", "rock_type": ""}], empty="keep"
        )

        assert outcomes(result) == [SKIP]

    def test_a_row_without_location_columns_reports_every_field_problem(
        self, run_import
    ):
        _, result = run_import(
            RockSample,
            [rock_row(weight_grams="heavy", hardness_mohs="hard")],
        )

        fields = set(result.rows[0].validation_error.error_dict)
        assert (outcomes(result), fields) == (
            [INVALID],
            {"weight_grams", "hardness_mohs"},
        )

    def test_a_row_with_location_columns_reports_every_field_problem_too(
        self, run_import
    ):
        _, result = run_import(
            RockSample,
            [
                rock_row(
                    weight_grams="heavy",
                    latitude="north",
                    longitude="12",
                )
            ],
        )

        fields = set(result.rows[0].validation_error.error_dict)
        assert (outcomes(result), fields) == ([INVALID], {"weight_grams", "location"})
        assert not RockSample.objects.filter(name="Granite").exists()

    def test_a_row_with_a_problem_does_not_stop_the_rows_after_it(self, run_import):
        _, result = run_import(
            RockSample,
            [rock_row(weight_grams="heavy"), rock_row(name="Basalt")],
        )

        assert outcomes(result) == [INVALID, NEW]


class TestDecimalComma:
    """A number written with a decimal comma needs changes, and nothing is written."""

    def test_the_cell_is_a_problem_on_its_column(self, run_import):
        _, result = run_import(RockSample, [rock_row(weight_grams="12,5")])

        assert outcomes(result) == [INVALID]
        assert set(result.rows[0].validation_error.error_dict) == {"weight_grams"}
        assert not RockSample.objects.filter(name="Granite").exists()


class TestSampleNameIgnored:
    """The sample name of a measurement file is written for readers and never read."""

    def test_a_sample_name_column_changes_nothing(self, run_import, open_dataset):
        sample = RockSampleFactory(dataset=open_dataset, local_id="S-1", name="Real")
        row = {"sample": sample.uuid, "element": "Fe", "concentration_ppm": "1.5"}

        _, plain = run_import(XRFMeasurement, [row], dry_run=True)
        _, named = run_import(
            XRFMeasurement, [{**row, "sample_name": "Another name"}], dry_run=True
        )

        sample.refresh_from_db()
        assert outcomes(plain) == outcomes(named) == [NEW]
        assert sample.name == "Real"


class TestMeasurementSample:
    """A measurement names its sample by portal ID, Local ID or a unique name."""

    @pytest.fixture
    def sample(self, open_dataset):
        """A sample of the dataset with a Local ID."""
        return RockSampleFactory(dataset=open_dataset, local_id="S-1", name="Core 14")

    def measurement(self, sample_cell):
        """Return the cells of a new measurement on a sample."""
        return {
            "sample": sample_cell,
            "element": "Fe",
            "concentration_ppm": "1.5",
        }

    def test_a_portal_id_of_a_sample_in_another_dataset_the_person_may_open(
        self, run_import
    ):
        public = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )

        _, result = run_import(XRFMeasurement, [self.measurement(public.uuid)])

        assert outcomes(result) == [NEW]
        assert result.rows[0].instance.sample == public

    def test_a_local_id_finds_a_sample_of_this_dataset(self, run_import, sample):
        _, result = run_import(XRFMeasurement, [self.measurement("S-1")])

        assert result.rows[0].instance.sample == sample

    def test_a_unique_name_finds_a_sample_of_this_dataset(self, run_import, sample):
        _, result = run_import(XRFMeasurement, [self.measurement("Core 14")])

        assert result.rows[0].instance.sample == sample

    def test_a_local_id_of_another_dataset_finds_nothing(self, run_import, sample):
        elsewhere = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        _, result = run_import(
            XRFMeasurement, [self.measurement("S-1")], dataset=elsewhere
        )

        assert outcomes(result) == [INVALID]
        assert "sample" in result.rows[0].validation_error.error_dict

    def test_a_shared_name_is_a_problem(self, run_import, open_dataset, sample):
        RockSampleFactory(dataset=open_dataset, name="Core 14")

        _, result = run_import(XRFMeasurement, [self.measurement("Core 14")])

        assert outcomes(result) == [INVALID]

    def test_a_sample_the_person_may_not_open_is_not_found(self, run_import):
        private = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        )

        _, result = run_import(XRFMeasurement, [self.measurement(private.uuid)])

        assert outcomes(result) == [INVALID]
        assert "sample" in result.rows[0].validation_error.error_dict


class TestSampleCache:
    """A file asks the database once for each sample its cells name."""

    @pytest.fixture
    def samples(self, open_dataset):
        """Three samples of the dataset."""
        return [
            RockSampleFactory(dataset=open_dataset, local_id=f"S-{n}") for n in range(3)
        ]

    def cost_of(self, schema, dataset, cells):
        """Count the queries a fresh sample widget needs to read the cells."""
        widget = schema.get("sample").widget(dataset=dataset)
        with CaptureQueriesContext(connection) as queries:
            for cell in cells:
                widget.clean(cell)
        return len(queries)

    def test_300_rows_over_three_samples_cost_three_lookups(
        self, open_dataset, samples
    ):
        schema = registry.get_for_model(XRFMeasurement).get_table_schema()
        distinct = [sample.uuid for sample in samples]

        once = self.cost_of(schema, open_dataset, distinct)
        many = self.cost_of(schema, open_dataset, distinct * 100)

        assert many == once

    def test_a_cell_read_twice_asks_nothing_the_second_time(
        self, open_dataset, samples, django_assert_num_queries
    ):
        schema = registry.get_for_model(XRFMeasurement).get_table_schema()
        widget = schema.get("sample").widget(dataset=open_dataset)
        widget.clean("S-1")

        with django_assert_num_queries(0):
            assert widget.clean("S-1") == samples[1]

    def test_a_refused_cell_is_refused_again_without_asking(
        self, open_dataset, django_assert_num_queries
    ):
        schema = registry.get_for_model(XRFMeasurement).get_table_schema()
        widget = schema.get("sample").widget(dataset=open_dataset)
        with pytest.raises(ValueError):
            widget.clean("nobody")

        with django_assert_num_queries(0), pytest.raises(ValueError):
            widget.clean("nobody")

    def test_a_new_widget_starts_with_an_empty_cache(self, open_dataset, samples):
        schema = registry.get_for_model(XRFMeasurement).get_table_schema()
        schema.get("sample").widget(dataset=open_dataset).clean("S-1")

        fresh = schema.get("sample").widget(dataset=open_dataset)

        assert fresh.clean("S-1") == samples[1]
        assert len(fresh.found) == 1


class TestChangedCells:
    """The cells a row changes are listed as column, label, old and new."""

    @pytest.fixture
    def rock(self, open_dataset):
        """A stored rock."""
        return RockSampleFactory(
            dataset=open_dataset,
            local_id="R-1",
            rock_type="granite",
            weight_grams=12.5,
        )

    def test_the_resource_keeps_the_changes_of_an_updated_row(self, run_import, rock):
        resource, _ = run_import(
            RockSample,
            [{"local_id": "R-1", "rock_type": "basalt", "weight_grams": "12.50"}],
        )

        changes = resource.changes[1]
        assert [change["column"] for change in changes] == ["rock_type"]
        assert changes[0]["old"] == "granite"
        assert changes[0]["new"] == "basalt"
        assert changes[0]["label"]

    def test_a_number_written_another_way_is_not_a_change(self, run_import, rock):
        resource, result = run_import(
            RockSample, [{"local_id": "R-1", "weight_grams": "12.500"}]
        )

        assert outcomes(result) == [SKIP]
        assert resource.changes[1] == []

    def test_a_new_row_has_no_changes_to_list(self, run_import):
        resource, _ = run_import(RockSample, [rock_row()])

        assert 1 not in resource.changes

    def test_changed_cells_compares_the_columns_the_row_has(self, rock):
        schema = registry.get_for_model(RockSample).get_table_schema()
        after = RockSample.objects.get(pk=rock.pk)
        after.rock_type = "basalt"
        after.weight_grams = 99

        changes = changed_cells(schema, rock, after, {"rock_type": "basalt"})

        assert [change["column"] for change in changes] == ["rock_type"]


class TestBuildResource:
    """The resource reads the columns the file has, in the dataset it is given."""

    def test_the_definition_builds_the_resource_of_its_type(self, open_dataset):
        definition = get_definition("rocksample")

        resource = definition.resource(open_dataset, mode="add", empty="clear")

        assert resource.dataset == open_dataset
        assert (resource.mode, resource.empty) == ("add", "clear")
        assert resource._meta.model is RockSample

    def test_a_column_the_file_lacks_is_not_a_field(self, open_dataset):
        schema = registry.get_for_model(RockSample).get_table_schema()

        resource = build_resource(
            schema, open_dataset, columns=["name", "rock_type", "latitude"]
        )

        assert {"name", "rock_type", "latitude"} <= set(resource.fields)
        assert "weight_grams" not in resource.fields

    def test_two_resources_do_not_share_a_sample_cache(self, open_dataset):
        schema = registry.get_for_model(XRFMeasurement).get_table_schema()

        first = build_resource(schema, open_dataset)
        second = build_resource(schema, open_dataset)

        assert first.fields["sample"].widget is not second.fields["sample"].widget


class TestPrivateDataset:
    """A private dataset imports like any other."""

    def test_rows_are_added_and_changed(self, run_import):
        private = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        rock = RockSampleFactory(dataset=private, local_id="R-1", rock_type="granite")

        _, result = run_import(
            RockSample,
            [{"local_id": "R-1", "rock_type": "basalt"}, rock_row(local_id="R-2")],
            dataset=private,
        )

        rock.refresh_from_db()
        assert (outcomes(result), rock.rock_type) == ([UPDATE, NEW], "basalt")


class TestEveryRegisteredType:
    """Every registered sample and measurement type imports a file (SC-006)."""

    @pytest.fixture
    def anchor(self, open_dataset):
        """A sample of the dataset, for the measurements to be made on."""
        return RockSampleFactory(dataset=open_dataset, local_id="ANCHOR")

    def row_for(self, schema, anchor):
        """Fill every required column of a type from the schema's examples."""
        row = {}
        for column in schema.importable:
            if column.role != "field" or not column.required:
                continue
            row[column.name] = column.example
        if "sample" in {column.name for column in schema.importable}:
            row["sample"] = anchor.uuid
        row["local_id"] = "NEW-1"
        return row

    @pytest.mark.parametrize(
        "model",
        [*registry.samples, *registry.measurements],
        ids=lambda model: model._meta.model_name,
    )
    def test_a_row_of_the_types_own_columns_is_added(self, run_import, anchor, model):
        schema = registry.get_for_model(model).get_table_schema()
        row = self.row_for(schema, anchor)

        _, result = run_import(model, [row])

        assert outcomes(result) == [NEW], result.rows[0].validation_error or [
            error.error for error in result.rows[0].errors
        ]
        assert model.objects.filter(local_id="NEW-1").count() == 1
        assert issubclass(model, Measurement) or model.objects.get(local_id="NEW-1")
