"""Tests for the location lookups in ``fairdm.utils.location.managers``."""

import re

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.measure import D
from django.db import connection

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Organization
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
)
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

    def test_a_box_that_crosses_the_180th_meridian_returns_the_samples_in_it(
        self, released
    ):
        west = RockSampleFactory(dataset=released, location=at(178, -15))
        east = RockSampleFactory(dataset=released, location=at(-178, -15))
        RockSampleFactory(dataset=released, location=at(0, -15))

        found = Sample.objects.inside((175, -20, -175, -10))

        assert set(found) == {west, east}

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


@pytest.mark.django_db
class TestMeasurementLookups:
    """AS 2.5, 2.6 and 2.8: a measurement is found by its own location, else its sample's for a viewer who may open the sample."""

    ROME = (12.5, 41.9)
    BERLIN = (13.4, 52.5)
    AROUND_ROME = (10, 40, 15, 45)
    AROUND_BERLIN = (12, 51, 15, 54)

    @pytest.fixture
    def sample(self, released):
        return RockSampleFactory(dataset=released, location=at(*self.ROME))

    def test_a_measurements_own_location_wins_over_its_samples(self, released, sample):
        own = ExampleMeasurementFactory(
            sample=sample, dataset=released, location=at(*self.BERLIN)
        )

        assert own in Measurement.objects.inside(self.AROUND_BERLIN)
        assert own not in Measurement.objects.inside(self.AROUND_ROME)

    def test_a_measurement_with_no_location_is_found_by_its_samples(
        self, released, sample
    ):
        inherited = ExampleMeasurementFactory(sample=sample, dataset=released)

        assert inherited in Measurement.objects.inside(self.AROUND_ROME)
        assert inherited not in Measurement.objects.inside(self.AROUND_BERLIN)

    def test_a_measurement_with_nothing_located_is_never_inside(self, released):
        bare = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=released), dataset=released
        )

        assert bare not in Measurement.objects.inside((-180, -90, 180, 90))

    def test_an_area_returns_each_measurement_once(self, released, sample):
        ExampleMeasurementFactory(sample=sample, dataset=released)
        ExampleMeasurementFactory(
            sample=sample, dataset=released, location=at(*self.ROME)
        )

        found = Measurement.objects.inside(self.AROUND_ROME)

        assert found.count() == 2

    def test_the_samples_location_is_not_used_for_a_viewer_who_may_not_open_it(
        self, released, hidden
    ):
        sample = RockSampleFactory(dataset=hidden, location=at(*self.ROME))
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)
        stranger = PersonFactory(is_active=True)

        for viewer in (None, AnonymousUser(), stranger):
            assert measurement not in Measurement.objects.inside(
                self.AROUND_ROME, user=viewer
            )

    def test_the_samples_location_is_used_for_a_viewer_who_may_open_it(
        self, released, hidden
    ):
        sample = RockSampleFactory(dataset=hidden, location=at(*self.ROME))
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)
        member = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=hidden, contributor=member, level=ContributionLevel.VIEW
        )

        found = Measurement.objects.inside(self.AROUND_ROME, user=member)

        assert measurement in found

    def test_a_hidden_sample_never_hides_a_measurements_own_location(
        self, released, hidden
    ):
        sample = RockSampleFactory(dataset=hidden, location=at(*self.ROME))
        measurement = ExampleMeasurementFactory(
            sample=sample, dataset=released, location=at(*self.BERLIN)
        )

        assert measurement in Measurement.objects.inside(self.AROUND_BERLIN)

    def test_within_distance_reads_the_effective_location(self, released, sample):
        own = ExampleMeasurementFactory(
            sample=sample, dataset=released, location=at(12.5, 42.9)
        )
        inherited = ExampleMeasurementFactory(sample=sample, dataset=released)

        found = Measurement.objects.within_distance(at(*self.ROME), D(km=10))

        assert set(found) == {inherited}
        assert own not in found

    def test_within_distance_withholds_a_hidden_samples_location(
        self, released, hidden
    ):
        sample = RockSampleFactory(dataset=hidden, location=at(*self.ROME))
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)

        found = Measurement.objects.within_distance(at(*self.ROME), 1_000, user=None)

        assert measurement not in found

    def test_nearest_orders_by_the_effective_location_and_carries_the_distance(
        self, released, sample
    ):
        inherited = ExampleMeasurementFactory(sample=sample, dataset=released)
        own = ExampleMeasurementFactory(
            sample=sample, dataset=released, location=at(12.5, 42.9)
        )
        bare = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=released), dataset=released
        )

        found = list(Measurement.objects.nearest(at(*self.ROME)))

        assert found == [inherited, own, bare]
        assert round(found[1].distance.km) == 111
        assert found[2].distance is None

    def test_nearest_withholds_a_hidden_samples_location(self, released, hidden):
        sample = RockSampleFactory(dataset=hidden, location=at(*self.ROME))
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)

        found = list(Measurement.objects.nearest(at(*self.ROME), user=None))

        assert found == [measurement]
        assert found[0].distance is None

    def test_the_lookups_combine_with_visible_to(self, released, hidden):
        visible = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=released),
            dataset=released,
            location=at(*self.ROME),
        )
        ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=hidden),
            dataset=hidden,
            location=at(*self.ROME),
        )

        found = Measurement.objects.visible_to(None).inside(self.AROUND_ROME)

        assert set(found) == {visible}


@pytest.mark.django_db
class TestQueryPlan:
    """SC-005 and FR-020: the area and distance lookups read a spatial index, not the whole table."""

    # With sequential scans switched off the planner takes an index whenever the query can use one, so
    # the plan answers "can the lookup use the index" and not "did the table statistics favour it".
    COUNT = 100
    AREA = (0, 0, 10, 10)
    CENTRE = at(5.0, 5.0)

    @staticmethod
    def place(i):
        """A grid of places across the globe, 50 columns by 2 rows."""
        return at(-180 + (i % 50) * 7.1, -70 + (i // 50) * 3.5)

    @pytest.fixture
    def portal(self, released):
        samples = Sample.objects.bulk_create(
            [
                Sample(dataset=released, name=f"s{i}", location=self.place(i))
                for i in range(self.COUNT)
            ]
        )
        Measurement.objects.bulk_create(
            [
                Measurement(
                    dataset=released,
                    sample=sample,
                    name=f"m{i}",
                    location=self.place(i + 7) if i % 2 else None,
                )
                for i, sample in enumerate(samples)
            ]
        )
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL enable_seqscan = off")

    @staticmethod
    def spatial_index_missing(queryset, model, whole_table_allowed=False):
        """Return what is wrong with the plan, or an empty string when it reads a spatial index."""
        plan = queryset.explain()
        table = model._meta.db_table
        if not re.search(
            rf"Index Scan (?:using|on) \S*location\S*(?: on {table})?\s", plan
        ):
            return f"{table} is not read through a location index:\n{plan}"
        if not whole_table_allowed and f"Seq Scan on {table} " in plan:
            return f"{table} is read whole:\n{plan}"
        return ""

    def test_the_area_and_distance_lookups_read_a_spatial_index(self, portal):
        lookups = {
            "samples inside an area": (Sample.objects.inside(self.AREA), Sample, False),
            "samples within a distance": (
                Sample.objects.within_distance(self.CENTRE, D(km=500)),
                Sample,
                False,
            ),
            # The measurements a sample places are joined on their sample, and the planner may read the
            # measurement table whole for that branch. The samples are never read whole.
            "measurements inside an area": (
                Measurement.objects.inside(self.AREA),
                Measurement,
                True,
            ),
            "measurements within a distance": (
                Measurement.objects.within_distance(self.CENTRE, D(km=500)),
                Measurement,
                True,
            ),
        }

        problems = [
            f"{name}: {problem}"
            for name, (queryset, model, whole_table_allowed) in lookups.items()
            if (
                problem := self.spatial_index_missing(
                    queryset, model, whole_table_allowed
                )
            )
        ]
        problems += [
            f"{name} (samples joined): {problem}"
            for name, (queryset, _, _) in lookups.items()
            if name.startswith("measurements")
            if (problem := self.spatial_index_missing(queryset, Sample))
        ]

        assert not problems, "\n".join(problems)
