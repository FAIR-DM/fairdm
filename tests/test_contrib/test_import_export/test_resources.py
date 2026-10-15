"""Tests for the location columns of the generated import and export resources."""

import pytest
import tablib
from django.contrib.gis.geos import Point
from import_export.fields import Field
from import_export.widgets import ForeignKeyWidget

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from demo.models import RockSample, XRFMeasurement
from fairdm.contrib.import_export.resources import MeasurementResource, SampleResource
from fairdm.core.models import Dataset, Sample
from fairdm.factories import DatasetFactory
from fairdm.utils.choices import Visibility
from fairdm.registry.config import ModelConfiguration

LOCATION_COLUMNS = ["latitude", "longitude", "location_elevation", "location_uncertainty"]


def at(longitude, latitude):
    return Point(longitude, latitude, srid=4326)


def reference(name, model):
    """A column that names the related record by its primary key."""
    return Field(
        attribute=name, column_name=name, widget=ForeignKeyWidget(model, "pk")
    )


def resource_for(model, target, fields, **references):
    generated = ModelConfiguration(model=model, fields=fields).get_resource_class()
    declared = {"dataset": reference("dataset", Dataset), **references}
    return type("Resource", (generated,), declared)(dataset=target)


def sample_resource(dataset):
    return resource_for(
        RockSample,
        dataset,
        ["id", "dataset", "name", "rock_type", "collection_date", "location"],
    )


def measurement_resource(dataset):
    return resource_for(
        XRFMeasurement,
        dataset,
        [
            "id",
            "dataset",
            "sample",
            "name",
            "element",
            "concentration_ppm",
            "location",
        ],
        sample=reference("sample", Sample),
    )


def rows(exported):
    return exported.dict


def public_dataset():
    """A dataset the generated resource's dataset column can see: ``Dataset.objects`` hides private ones."""
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


@pytest.fixture
def dataset(db):
    return public_dataset()


@pytest.mark.django_db
class TestExport:
    """AS 5.1 and 5.5: each row carries the record's own location, and none when it has none."""

    def test_a_sample_exports_its_location_in_four_columns(self, dataset):
        RockSampleFactory(
            dataset=dataset,
            location=at(8.4115, 49.0094),
            location_elevation=112.5,
            location_uncertainty=25.0,
        )

        exported = sample_resource(dataset).export(
            queryset=RockSample.objects.filter(dataset=dataset)
        )

        assert set(LOCATION_COLUMNS) <= set(exported.headers)
        assert "location" not in exported.headers
        (row,) = rows(exported)
        assert row["latitude"] == pytest.approx(49.0094)
        assert row["longitude"] == pytest.approx(8.4115)
        assert row["location_elevation"] == pytest.approx(112.5)
        assert row["location_uncertainty"] == pytest.approx(25.0)

    def test_a_sample_without_a_location_exports_empty_columns(self, dataset):
        RockSampleFactory(dataset=dataset)

        exported = sample_resource(dataset).export(
            queryset=RockSample.objects.filter(dataset=dataset)
        )

        (row,) = rows(exported)
        assert [row[column] for column in LOCATION_COLUMNS] == ["", "", "", ""]

    def test_a_measurement_exports_only_its_own_location(self, dataset):
        placed = RockSampleFactory(dataset=dataset, location=at(8.0, 49.0))
        own = XRFMeasurementFactory(
            dataset=dataset, sample=placed, location=at(9.5, 50.5)
        )
        without = XRFMeasurementFactory(dataset=dataset, sample=placed)

        exported = measurement_resource(dataset).export(
            queryset=XRFMeasurement.objects.filter(dataset=dataset)
        )

        by_id = {int(row["id"]): row for row in rows(exported)}
        assert by_id[own.pk]["latitude"] == pytest.approx(50.5)
        assert by_id[own.pk]["longitude"] == pytest.approx(9.5)
        assert [by_id[without.pk][column] for column in LOCATION_COLUMNS] == [
            "",
            "",
            "",
            "",
        ]


@pytest.mark.django_db
class TestImport:
    """AS 5.2 to 5.4: import reads the columns in any notation and refuses what it cannot read."""

    def row(self, dataset, **cells):
        return {
            "id": "",
            "dataset": dataset.pk,
            "name": "RS-1",
            "rock_type": "basalt",
            "collection_date": "2026-01-02",
            "latitude": "",
            "longitude": "",
            "location_elevation": "",
            "location_uncertainty": "",
            **cells,
        }

    def load(self, resource, *records, dry_run=False):
        headers = list(records[0])
        data = tablib.Dataset(
            *[[record[header] for header in headers] for record in records],
            headers=headers,
        )
        return resource.import_data(data, dry_run=dry_run, raise_errors=False)

    def test_an_exported_file_imports_with_the_locations_it_was_exported_with(
        self, dataset
    ):
        RockSampleFactory(
            dataset=dataset,
            name="placed",
            location=at(8.4115, 49.0094),
            location_elevation=112.5,
            location_uncertainty=25.0,
        )
        RockSampleFactory(dataset=dataset, name="unplaced")
        resource = sample_resource(dataset)
        exported = resource.export(queryset=RockSample.objects.filter(dataset=dataset))
        target = public_dataset()
        records = [{**row, "id": "", "dataset": target.pk} for row in rows(exported)]

        result = self.load(sample_resource(target), *records)

        assert not result.has_errors()
        assert not result.has_validation_errors()
        placed = RockSample.objects.get(dataset=target, name="placed")
        assert placed.location.x == pytest.approx(8.4115)
        assert placed.location.y == pytest.approx(49.0094)
        assert placed.location.srid == 4326
        assert placed.location_elevation == pytest.approx(112.5)
        assert placed.location_uncertainty == pytest.approx(25.0)
        unplaced = RockSample.objects.get(dataset=target, name="unplaced")
        assert unplaced.location is None
        assert unplaced.location_elevation is None
        assert unplaced.location_uncertainty is None

    @pytest.mark.parametrize(
        ("latitude", "longitude"),
        [
            ("48.93528", "8.4115"),
            ("48 56.117", "8 24.69"),
            ("48°56'7\"N", "8°24'41.4\"E"),
            ("N 48 56 7", "E 8 24 41.4"),
        ],
    )
    def test_every_notation_imports_as_the_same_decimal_degrees(
        self, dataset, latitude, longitude
    ):
        result = self.load(
            sample_resource(dataset),
            self.row(dataset, latitude=latitude, longitude=longitude),
        )

        assert not result.has_validation_errors()
        sample = RockSample.objects.get(dataset=dataset)
        assert sample.location.y == pytest.approx(48.93528, abs=1e-4)
        assert sample.location.x == pytest.approx(8.4115, abs=1e-4)

    @pytest.mark.parametrize(
        ("cells", "value"),
        [
            ({"latitude": "north of here", "longitude": "8.4"}, "north of here"),
            ({"latitude": "91", "longitude": "8.4"}, "91"),
            ({"latitude": "49.0", "longitude": "181"}, "181"),
            ({"latitude": "49.0", "longitude": ""}, None),
            ({"location_elevation": "112", "latitude": "", "longitude": ""}, None),
            (
                {
                    "latitude": "49.0",
                    "longitude": "8.4",
                    "location_uncertainty": "-3",
                },
                None,
            ),
        ],
    )
    def test_a_row_that_cannot_be_read_is_reported_and_not_saved(
        self, dataset, cells, value
    ):
        result = self.load(
            sample_resource(dataset),
            self.row(dataset, name="good", latitude="49.0", longitude="8.4"),
            self.row(dataset, name="bad", **cells),
        )

        assert result.has_validation_errors()
        (invalid,) = result.invalid_rows
        assert invalid.number == 2
        if value is not None:
            assert value in " ".join(invalid.error.messages)
        assert not RockSample.objects.filter(dataset=dataset, name="bad").exists()

    def test_a_file_without_the_columns_leaves_the_location_as_it_was(self, dataset):
        sample = RockSampleFactory(dataset=dataset, location=at(8.0, 49.0))
        row = {"id": sample.pk, "dataset": dataset.pk, "name": "renamed"}
        row.update(rock_type=sample.rock_type, collection_date="2026-01-02")

        result = self.load(sample_resource(dataset), row)

        assert not result.has_validation_errors()
        sample.refresh_from_db()
        assert sample.name == "renamed"
        assert sample.location.x == pytest.approx(8.0)
        assert sample.location.y == pytest.approx(49.0)

    def test_a_measurement_row_sets_the_measurements_own_location(self, dataset):
        sample = RockSampleFactory(dataset=dataset, location=at(8.0, 49.0))
        row = {
            "id": "",
            "dataset": dataset.pk,
            "sample": sample.pk,
            "name": "XRF-1",
            "element": "Fe",
            "concentration_ppm": "12.5",
            "latitude": "50.5",
            "longitude": "9.5",
            "location_elevation": "",
            "location_uncertainty": "",
        }

        result = self.load(measurement_resource(dataset), row)

        assert not result.has_validation_errors()
        measurement = XRFMeasurement.objects.get(dataset=dataset)
        assert measurement.location.y == pytest.approx(50.5)
        assert measurement.location.x == pytest.approx(9.5)


@pytest.mark.django_db
class TestHandWrittenResources:
    """The shipped resources expand a listed ``location`` into the same four columns."""

    def test_a_sample_resource_listing_location_exports_the_four_columns(self, dataset):
        class RockResource(SampleResource):
            class Meta:
                model = RockSample
                fields = ("id", "name", "location")

        RockSampleFactory(
            dataset=dataset,
            location=at(8.4115, 49.0094),
            location_elevation=112.5,
            location_uncertainty=25.0,
        )

        exported = RockResource(dataset).export(
            queryset=RockSample.objects.filter(dataset=dataset)
        )

        assert "location" not in exported.headers
        (row,) = rows(exported)
        assert row["latitude"] == pytest.approx(49.0094)
        assert row["longitude"] == pytest.approx(8.4115)
        assert row["location_elevation"] == pytest.approx(112.5)
        assert row["location_uncertainty"] == pytest.approx(25.0)

    def test_a_measurement_resource_listing_location_exports_only_its_own(
        self, dataset
    ):
        class XRFResource(MeasurementResource):
            class Meta:
                model = XRFMeasurement
                fields = ("id", "name", "location")

        placed = RockSampleFactory(dataset=dataset, location=at(8.0, 49.0))
        XRFMeasurementFactory(dataset=dataset, sample=placed)

        exported = XRFResource(dataset).export(
            queryset=XRFMeasurement.objects.filter(dataset=dataset)
        )

        (row,) = rows(exported)
        assert [row[column] for column in LOCATION_COLUMNS] == ["", "", "", ""]
