"""Tests for spatial coverage in ``fairdm.utils.location.coverage``."""

import pytest
from django.contrib.gis.geos import Point

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory
from fairdm.utils.choices import Visibility
from fairdm.utils.location.coverage import Coverage, spatial_coverage


def at(longitude, latitude):
    return Point(longitude, latitude, srid=4326)


@pytest.fixture
def dataset(db):
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


@pytest.mark.django_db
class TestSpatialCoverage:
    """FR-021 and FR-022: the smallest box holding every location, narrower across the 180th meridian."""

    def test_the_box_holds_every_location(self, dataset):
        RockSampleFactory(dataset=dataset, location=at(12.5, 41.9))
        RockSampleFactory(dataset=dataset, location=at(-3.0, 52.5))
        RockSampleFactory(dataset=dataset, location=at(30.0, -10.0))

        found = spatial_coverage((Sample.objects.all(), "location"))

        assert found == Coverage(west=-3.0, south=-10.0, east=30.0, north=52.5)

    def test_it_is_none_when_nothing_is_located(self, dataset):
        RockSampleFactory(dataset=dataset)

        assert spatial_coverage((Sample.objects.all(), "location")) is None

    def test_it_is_none_for_no_records_at_all(self, db):
        assert spatial_coverage((Sample.objects.none(), "location")) is None

    def test_a_single_location_is_a_box_of_no_width(self, dataset):
        RockSampleFactory(dataset=dataset, location=at(8.4, 48.9))

        found = spatial_coverage((Sample.objects.all(), "location"))

        assert found == Coverage(west=8.4, south=48.9, east=8.4, north=48.9)

    def test_locations_either_side_of_the_180th_meridian_make_a_narrow_box(
        self, dataset
    ):
        RockSampleFactory(dataset=dataset, location=at(175.0, -20.0))
        RockSampleFactory(dataset=dataset, location=at(-175.0, -10.0))
        RockSampleFactory(dataset=dataset, location=at(178.0, -15.0))

        found = spatial_coverage((Sample.objects.all(), "location"))

        assert found.west == 175.0
        assert found.east == -175.0
        assert found.west > found.east
        assert (found.south, found.north) == (-20.0, -10.0)

    def test_a_crossing_box_is_less_than_ten_degrees_wide(self, dataset):
        RockSampleFactory(dataset=dataset, location=at(176.0, 0.0))
        RockSampleFactory(dataset=dataset, location=at(-179.0, 0.0))

        found = spatial_coverage((Sample.objects.all(), "location"))

        assert (found.east - found.west) % 360 < 10

    def test_locations_that_do_not_cross_keep_the_plain_box(self, dataset):
        RockSampleFactory(dataset=dataset, location=at(-170.0, 10.0))
        RockSampleFactory(dataset=dataset, location=at(-160.0, 20.0))

        found = spatial_coverage((Sample.objects.all(), "location"))

        assert found == Coverage(west=-170.0, south=10.0, east=-160.0, north=20.0)

    def test_locations_spread_round_the_globe_keep_the_wider_plain_box(self, dataset):
        RockSampleFactory(dataset=dataset, location=at(-90.0, 0.0))
        RockSampleFactory(dataset=dataset, location=at(0.0, 0.0))
        RockSampleFactory(dataset=dataset, location=at(90.0, 0.0))

        found = spatial_coverage((Sample.objects.all(), "location"))

        assert (found.west, found.east) == (-90.0, 90.0)

    def test_several_querysets_are_merged_into_one_box(self, dataset):
        sample = RockSampleFactory(dataset=dataset, location=at(10.0, 10.0))
        ExampleMeasurementFactory(
            sample=sample, dataset=dataset, location=at(20.0, 30.0)
        )

        found = spatial_coverage(
            (Sample.objects.all(), "location"),
            (Measurement.objects.all(), "location"),
        )

        assert found == Coverage(west=10.0, south=10.0, east=20.0, north=30.0)

    def test_a_crossing_box_is_found_across_several_querysets(self, dataset):
        sample = RockSampleFactory(dataset=dataset, location=at(179.0, 0.0))
        ExampleMeasurementFactory(
            sample=sample, dataset=dataset, location=at(-179.0, 5.0)
        )

        found = spatial_coverage(
            (Sample.objects.all(), "location"),
            (Measurement.objects.all(), "location"),
        )

        assert (found.west, found.east) == (179.0, -179.0)

    def test_a_queryset_with_nothing_located_adds_nothing(self, dataset):
        RockSampleFactory(dataset=dataset, location=at(10.0, 10.0))

        found = spatial_coverage(
            (Sample.objects.all(), "location"),
            (Measurement.objects.all(), "location"),
        )

        assert found == Coverage(west=10.0, south=10.0, east=10.0, north=10.0)
