"""US9: loading many measurements without a query for each.

FR-046 requires that loading measurements together with their datasets, samples and
contributors, and loading them together with their descriptions, dates and identifiers,
each take a number of queries that does not grow with the number of measurements. FR-047
requires both to combine with each other and with ordinary filtering and ordering.

The tests already in ``test_models.py`` do not establish this. One creates a single
measurement and asserts ``queries_with <= 4`` - a bound the unoptimised path already
meets for one row, as its own comment admits ("For a single measurement, prefetch may
add overhead. The benefit shows with multiple measurements."). Another asserts
``num_queries <= 10`` against 100 rows created but touches only the first ten and counts
once - a ceiling measured at one size is not a growth bound. Its chain test never orders.

These tests establish the property the way it must be established: by counting queries
at two different sizes and comparing, and by exercising both loadings together with
filter() AND order_by() at once.

Landed as a new file (mirroring ``managers.py``, per ``craft-tdd``'s "mirror the source
tree" rule), not in ``test_models.py`` - that file is owned by a concurrently running
story.
"""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.factories import PersonFactory
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory


def build_measurements_with_related(dataset, count):
    """Create `count` measurements in `dataset`, each with its own sample and one
    active contributor - the three relations `with_related()` prefetches."""
    measurements = []
    for _ in range(count):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=dataset), dataset=dataset
        )
        # ~1 in 5 PersonFactory instances are inactive by default; pin it so a
        # permission-adjacent read never turns this into an intermittent failure.
        measurement.add_contributor(
            PersonFactory(is_active=True), with_roles=["Creator"]
        )
        measurements.append(measurement)
    return measurements


def build_measurements_with_metadata(dataset, count):
    """Create `count` measurements in `dataset`, each with one description, one date
    and one identifier - the three relations `with_metadata()` prefetches."""
    measurements = []
    for i in range(count):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=dataset), dataset=dataset
        )
        MeasurementDescription.objects.create(
            related=measurement, type="MeasurementSetup", value=f"Method {i}"
        )
        MeasurementDate.objects.create(
            related=measurement, type="Setup", value="2024-01-15"
        )
        MeasurementIdentifier.objects.create(
            related=measurement, type="DOI", value=f"10.1234/meas.{dataset.pk}.{i}"
        )
        measurements.append(measurement)
    return measurements


def count_queries_accessing_related(queryset):
    """Evaluate `queryset` and touch sample, dataset and contributors on every row."""
    with CaptureQueriesContext(connection) as context:
        for measurement in queryset:
            _ = measurement.sample.name
            _ = measurement.dataset.name
            _ = list(measurement.contributors.all())
    return len(context.captured_queries)


def count_queries_accessing_metadata(queryset):
    """Evaluate `queryset` and touch descriptions, dates and identifiers on every row."""
    with CaptureQueriesContext(connection) as context:
        for measurement in queryset:
            _ = list(measurement.descriptions.all())
            _ = list(measurement.dates.all())
            _ = list(measurement.identifiers.all())
    return len(context.captured_queries)


@pytest.mark.django_db
class TestWithRelatedQueryCountDoesNotGrow:
    """T104 (FR-046): `with_related()` takes a query count that does not grow with the
    number of measurements, proven by counting at two sizes and comparing."""

    def test_query_count_is_equal_at_two_sizes(self, dataset, second_dataset):
        build_measurements_with_related(dataset, count=5)
        build_measurements_with_related(second_dataset, count=25)

        queries_at_5 = count_queries_accessing_related(
            Measurement.objects.with_related().filter(dataset=dataset)
        )
        queries_at_25 = count_queries_accessing_related(
            Measurement.objects.with_related().filter(dataset=second_dataset)
        )

        assert queries_at_5 == queries_at_25


@pytest.mark.django_db
class TestWithMetadataQueryCountDoesNotGrow:
    """T106 (FR-046): `with_metadata()` takes a query count that does not grow with
    the number of measurements, proven by counting at two sizes and comparing."""

    def test_query_count_is_equal_at_two_sizes(self, dataset, second_dataset):
        build_measurements_with_metadata(dataset, count=5)
        build_measurements_with_metadata(second_dataset, count=25)

        queries_at_5 = count_queries_accessing_metadata(
            Measurement.objects.with_metadata().filter(dataset=dataset)
        )
        queries_at_25 = count_queries_accessing_metadata(
            Measurement.objects.with_metadata().filter(dataset=second_dataset)
        )

        assert queries_at_5 == queries_at_25


@pytest.mark.django_db
class TestWithMetadataPrefetchesRecords:
    """T107 (FR-046): `with_metadata()` is defined on the queryset and genuinely
    prefetches descriptions, dates and identifiers - proven directly by showing
    access to those relations costs nothing once the queryset has been evaluated,
    in contrast to the same access against an unoptimised queryset."""

    def test_relations_cost_nothing_to_access_after_evaluation(self, dataset):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=dataset), dataset=dataset
        )
        MeasurementDescription.objects.create(
            related=measurement, type="MeasurementSetup", value="XRF analysis"
        )
        MeasurementDate.objects.create(
            related=measurement, type="Setup", value="2024-01-15"
        )
        MeasurementIdentifier.objects.create(
            related=measurement, type="DOI", value="10.1234/meas.1"
        )

        (loaded,) = list(Measurement.objects.with_metadata().filter(pk=measurement.pk))

        with CaptureQueriesContext(connection) as context:
            assert list(loaded.descriptions.all())
            assert list(loaded.dates.all())
            assert list(loaded.identifiers.all())

        assert len(context.captured_queries) == 0

    def test_without_with_metadata_the_same_access_requeries(self, dataset):
        """Contrast: the same access pattern against a plain queryset does hit the
        database, so the zero-query result above is `with_metadata()` prefetching,
        not an artefact of some other cache."""
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=dataset), dataset=dataset
        )
        MeasurementDescription.objects.create(
            related=measurement, type="MeasurementSetup", value="XRF analysis"
        )

        (loaded,) = list(Measurement.objects.filter(pk=measurement.pk))

        with CaptureQueriesContext(connection) as context:
            list(loaded.descriptions.all())

        assert len(context.captured_queries) == 1


@pytest.mark.django_db
class TestBothLoadingsComposeWithFilteringAndOrdering:
    """T108 (FR-047): `with_related()` and `with_metadata()` compose with each other
    and with ordinary `filter()` and `order_by()` - and the combination filters and
    orders correctly. The existing chain test (`test_models.py`) never orders, so
    this is the first test exercising that half of FR-047."""

    def test_composed_queryset_filters_and_orders_correctly(
        self, dataset, second_dataset
    ):
        names = ["Charlie", "Alpha", "Bravo"]
        measurements = []
        for name in names:
            measurement = ExampleMeasurementFactory(
                sample=RockSampleFactory(dataset=dataset), dataset=dataset, name=name
            )
            measurement.add_contributor(
                PersonFactory(is_active=True), with_roles=["Creator"]
            )
            MeasurementDescription.objects.create(
                related=measurement, type="MeasurementSetup", value="Method"
            )
            measurements.append(measurement)

        # In a different dataset, so the filter below must exclude it.
        excluded = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=second_dataset),
            dataset=second_dataset,
            name="Zulu",
        )

        composed = (
            Measurement.objects.with_related()
            .with_metadata()
            .filter(dataset=dataset)
            .order_by("name")
        )

        results = list(composed)

        assert [m.name for m in results] == ["Alpha", "Bravo", "Charlie"]
        assert excluded.pk not in [m.pk for m in results]

        # Both prefetches still function after composing with filter() and order_by().
        with CaptureQueriesContext(connection) as context:
            for measurement in results:
                _ = measurement.sample.name
                _ = measurement.dataset.name
                _ = list(measurement.contributors.all())
                _ = list(measurement.descriptions.all())

        assert len(context.captured_queries) == 0
