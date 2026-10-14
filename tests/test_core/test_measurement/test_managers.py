"""Tests for the measurement queryset and manager."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point as GEOSPoint
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.factories import ContributionFactory, DatasetFactory, PersonFactory
from fairdm.utils.choices import Visibility


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


@pytest.mark.django_db
class TestVisibleTo:
    """FR-020: a measurement follows its own dataset, whatever the state of its sample's."""

    @pytest.fixture
    def measurements(self):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        return {
            "released": ExampleMeasurementFactory(
                sample=sample,
                dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True),
            ),
            "unpublished": ExampleMeasurementFactory(
                sample=sample,
                dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=False),
            ),
            "private": ExampleMeasurementFactory(
                sample=sample,
                dataset=DatasetFactory(visibility=Visibility.PRIVATE, published=False),
            ),
        }

    def test_a_visitor_sees_only_measurements_in_public_published_datasets(
        self, measurements
    ):
        visible = Measurement.objects.visible_to(AnonymousUser())

        assert set(visible) == {measurements["released"]}

    def test_a_published_sample_does_not_release_a_measurement_in_an_unpublished_dataset(
        self, measurements
    ):
        assert measurements["unpublished"] not in Measurement.objects.visible_to(
            AnonymousUser()
        )

    def test_a_signed_in_user_with_no_rights_sees_the_same_as_a_visitor(
        self, measurements
    ):
        visible = Measurement.objects.visible_to(PersonFactory(is_active=True))

        assert set(visible) == {measurements["released"]}

    def test_a_dataset_team_member_also_sees_that_datasets_measurements(
        self, measurements
    ):
        user = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=measurements["private"].dataset,
            contributor=user,
            level=ContributionLevel.VIEW,
        )

        visible = Measurement.objects.visible_to(user)

        assert set(visible) == {measurements["released"], measurements["private"]}

    def test_no_user_at_all_is_treated_as_a_visitor(self, measurements):
        assert set(Measurement.objects.visible_to(None)) == {measurements["released"]}


@pytest.mark.django_db
class TestWithEffectiveLocation:
    """FR-013 and FR-014 on a queryset: own location, else the sample's for a viewer who may open it."""

    @pytest.fixture
    def released(self):
        return DatasetFactory(visibility=Visibility.PUBLIC, published=True)

    @pytest.fixture
    def hidden(self):
        return DatasetFactory(visibility=Visibility.PRIVATE, published=False)

    def located(self, queryset, user=None):
        found = queryset.with_effective_location(user)
        return {m.pk: m.effective_location for m in found}

    def test_a_measurement_is_given_its_own_location_before_its_samples(
        self, released
    ):
        sample = RockSampleFactory(
            dataset=released, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        own = ExampleMeasurementFactory(
            sample=sample, dataset=released, location=GEOSPoint(1.0, 2.0, srid=4326)
        )
        inherited = ExampleMeasurementFactory(sample=sample, dataset=released)

        found = self.located(Measurement.objects.all())

        assert (found[own.pk].x, found[own.pk].y) == (1.0, 2.0)
        assert (found[inherited.pk].x, found[inherited.pk].y) == (12.5, 41.5)

    def test_a_measurement_with_nothing_located_is_given_none(self, released):
        sample = RockSampleFactory(dataset=released)
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)

        assert self.located(Measurement.objects.all())[measurement.pk] is None

    def test_the_samples_location_is_withheld_from_a_viewer_who_may_not_open_it(
        self, released, hidden
    ):
        sample = RockSampleFactory(
            dataset=hidden, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)
        stranger = PersonFactory(is_active=True)

        for viewer in (None, AnonymousUser(), stranger):
            assert self.located(Measurement.objects.all(), viewer)[measurement.pk] is None

    def test_the_samples_location_is_given_to_a_viewer_who_may_open_it(
        self, released, hidden
    ):
        sample = RockSampleFactory(
            dataset=hidden, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)
        member = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=hidden, contributor=member, level=ContributionLevel.VIEW
        )

        found = self.located(Measurement.objects.all(), member)

        assert (found[measurement.pk].x, found[measurement.pk].y) == (12.5, 41.5)

    def test_the_number_of_queries_does_not_grow_with_the_rows(self, released):
        sample = RockSampleFactory(
            dataset=released, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        ExampleMeasurementFactory(sample=sample, dataset=released)

        with CaptureQueriesContext(connection) as one:
            list(Measurement.objects.with_effective_location(None))
        for _ in range(3):
            ExampleMeasurementFactory(sample=sample, dataset=released)
        with CaptureQueriesContext(connection) as several:
            list(Measurement.objects.with_effective_location(None))

        assert len(several.captured_queries) == len(one.captured_queries)
