"""Tests for the measurement queryset and manager."""

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.factories import DatasetFactory, PersonFactory


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
class TestPublished:
    def test_published_excludes_a_measurement_whose_own_dataset_is_unpublished_even_though_its_sample_is_published(
        self, sample
    ):
        sample.dataset.published = True
        sample.dataset.save()
        measurement = ExampleMeasurementFactory(
            sample=sample, dataset=DatasetFactory(published=False)
        )

        assert measurement not in Measurement.objects.published()

    def test_published_includes_a_measurement_whose_own_dataset_is_published_even_though_its_sample_is_unpublished(
        self, sample
    ):
        # `sample` fixture's dataset is left at the model default, unpublished.
        measurement = ExampleMeasurementFactory(
            sample=sample, dataset=DatasetFactory(published=True)
        )

        assert measurement in Measurement.objects.published()


@pytest.mark.django_db
class TestManagerRefusesABareMeasurement:
    def test_manager_create_refuses_a_bare_measurement(self, dataset, sample):
        with pytest.raises(ValidationError):
            Measurement.objects.create(name="Direct", dataset=dataset, sample=sample)

    def test_direct_save_refuses_a_bare_measurement(self, dataset, sample):
        measurement = Measurement(name="Direct", dataset=dataset, sample=sample)

        with pytest.raises(ValidationError):
            measurement.save()

    def test_fixture_loading_refuses_a_bare_measurement(self, dataset, sample):
        from django.core import serializers

        payload = (
            '[{"model": "measurement.measurement", "pk": null, '
            f'"fields": {{"name": "Direct", "dataset": {dataset.pk}, "sample": {sample.pk}}}}}]'
        )
        (deserialized,) = serializers.deserialize("json", payload)

        with pytest.raises(ValidationError):
            deserialized.save()


@pytest.mark.django_db
class TestWithRelatedQueryCountDoesNotGrow:
    def test_query_count_is_equal_at_two_sizes(
        self, dataset, second_dataset, build_measurements_with_related
    ):
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
    def test_query_count_is_equal_at_two_sizes(
        self, dataset, second_dataset, build_measurements_with_metadata
    ):
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

        with CaptureQueriesContext(connection) as context:
            for measurement in results:
                _ = measurement.sample.name
                _ = measurement.dataset.name
                _ = list(measurement.contributors.all())
                _ = list(measurement.descriptions.all())

        assert len(context.captured_queries) == 0
