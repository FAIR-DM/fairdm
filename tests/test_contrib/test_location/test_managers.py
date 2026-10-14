"""Tests for the location lookups in ``fairdm.contrib.location.managers``."""

import pytest
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D

from demo.factories import RockSampleFactory
from fairdm.contrib.contributors.models import Organization
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory, OrganizationFactory
from fairdm.utils.choices import Visibility


def at(longitude, latitude):
    return Point(longitude, latitude, srid=4326)


@pytest.fixture
def released(db):
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


@pytest.fixture
def hidden(db):
    return DatasetFactory(visibility=Visibility.PRIVATE, published=False)


@pytest.mark.django_db
class TestSampleInside:
    """AS 2.1, 2.2 and 2.7: an area returns exactly the samples inside it, edge included."""

    @pytest.fixture
    def samples(self, released):
        return {
            "rome": RockSampleFactory(dataset=released, location=at(12.5, 41.9)),
            "berlin": RockSampleFactory(dataset=released, location=at(13.4, 52.5)),
            "paris": RockSampleFactory(dataset=released, location=at(2.35, 48.85)),
            "edge": RockSampleFactory(dataset=released, location=at(10.0, 41.0)),
            "nowhere": RockSampleFactory(dataset=released),
        }

    def test_a_box_returns_the_samples_inside_it_and_those_on_its_edge(self, samples):
        found = Sample.objects.inside((10, 40, 15, 45))

        assert set(found) == {samples["rome"], samples["edge"]}

    def test_a_polygon_returns_the_samples_inside_it_and_not_those_beyond_a_slanted_side(
        self, samples
    ):
        triangle = Polygon(((0, 40), (20, 40), (10, 60), (0, 40)), srid=4326)

        found = Sample.objects.inside(triangle)

        assert set(found) == {samples["rome"], samples["berlin"], samples["edge"]}

    def test_a_sample_with_no_location_is_never_inside(self, samples):
        found = Sample.objects.inside((-180, -90, 180, 90))

        assert samples["nowhere"] not in found

    def test_the_lookup_combines_with_other_filters(self, samples):
        found = Sample.objects.inside((10, 40, 15, 45)).filter(pk=samples["rome"].pk)

        assert list(found) == [samples["rome"]]


@pytest.mark.django_db
class TestSampleWithinDistance:
    """AS 2.3: samples within a distance, measured on the ground, near the equator and near the pole."""

    def test_metres_at_the_equator(self, released):
        near = RockSampleFactory(dataset=released, location=at(0.08, 0.0))
        far = RockSampleFactory(dataset=released, location=at(0.09, 0.0))

        found = Sample.objects.within_distance(at(0.0, 0.0), 10_000)

        assert near in found
        assert far not in found

    def test_a_measure_in_kilometres_at_the_equator(self, released):
        near = RockSampleFactory(dataset=released, location=at(0.0, 0.08))
        far = RockSampleFactory(dataset=released, location=at(0.0, 0.1))

        found = Sample.objects.within_distance(at(0.0, 0.0), D(km=10))

        assert near in found
        assert far not in found

    def test_a_degree_of_longitude_is_shorter_at_70_north(self, released):
        near = RockSampleFactory(dataset=released, location=at(0.2, 70.0))
        far = RockSampleFactory(dataset=released, location=at(0.3, 70.0))

        found = Sample.objects.within_distance(at(0.0, 70.0), D(km=10))

        assert near in found
        assert far not in found

    def test_a_sample_with_no_location_is_never_within(self, released):
        nowhere = RockSampleFactory(dataset=released)

        assert nowhere not in Sample.objects.within_distance(at(0.0, 0.0), 1_000_000)


@pytest.mark.django_db
class TestSampleNearest:
    """AS 2.4: nearest orders by distance and carries the distance."""

    def test_samples_come_nearest_first_with_the_distance_to_each(self, released):
        middle = RockSampleFactory(dataset=released, location=at(0.0, 0.5))
        far = RockSampleFactory(dataset=released, location=at(0.0, 1.0))
        close = RockSampleFactory(dataset=released, location=at(0.0, 0.1))

        found = list(Sample.objects.nearest(at(0.0, 0.0)))

        assert found == [close, middle, far]
        assert [round(s.distance.km) for s in found] == [11, 55, 111]

    def test_samples_with_no_location_come_last(self, released):
        nowhere = RockSampleFactory(dataset=released)
        placed = RockSampleFactory(dataset=released, location=at(5.0, 5.0))

        found = list(Sample.objects.nearest(at(0.0, 0.0)))

        assert found == [placed, nowhere]
        assert found[1].distance is None


@pytest.mark.django_db
class TestSampleLookupsWithVisibility:
    """AS 2.8: the lookups combine with ``visible_to``, in either order."""

    @pytest.fixture
    def samples(self, released, hidden):
        return {
            "released": RockSampleFactory(dataset=released, location=at(12.5, 41.9)),
            "hidden": RockSampleFactory(dataset=hidden, location=at(12.6, 41.8)),
        }

    def test_inside_then_visible_to_leaves_out_what_the_viewer_may_not_open(
        self, samples
    ):
        found = Sample.objects.inside((10, 40, 15, 45)).visible_to(None)

        assert set(found) == {samples["released"]}

    def test_visible_to_then_inside_leaves_out_what_the_viewer_may_not_open(
        self, samples
    ):
        found = Sample.objects.visible_to(None).inside((10, 40, 15, 45))

        assert set(found) == {samples["released"]}

    def test_within_distance_and_nearest_follow_visible_to(self, samples):
        point = at(12.5, 41.9)

        within = Sample.objects.visible_to(None).within_distance(point, D(km=50))
        nearest = Sample.objects.visible_to(None).nearest(point)

        assert set(within) == {samples["released"]}
        assert list(nearest) == [samples["released"]]


@pytest.mark.django_db
class TestOrganizationLookups:
    """AS 2.1 to 2.4 for organizations, which hold a plain point."""

    @pytest.fixture
    def organizations(self):
        return {
            "rome": OrganizationFactory(location=at(12.5, 41.9)),
            "berlin": OrganizationFactory(location=at(13.4, 52.5)),
            "nowhere": OrganizationFactory(),
        }

    def test_inside_returns_the_organizations_in_the_area(self, organizations):
        found = Organization.objects.inside((10, 40, 15, 45))

        assert set(found) == {organizations["rome"]}

    def test_within_distance_measures_on_the_ground(self, organizations):
        found = Organization.objects.within_distance(at(12.5, 42.4), D(km=100))

        assert set(found) == {organizations["rome"]}

    def test_nearest_orders_by_distance_and_carries_it(self, organizations):
        found = list(Organization.objects.nearest(at(12.5, 42.0)))

        assert found[:2] == [organizations["rome"], organizations["berlin"]]
        assert round(found[0].distance.km) == 11
        assert found[2] == organizations["nowhere"]
