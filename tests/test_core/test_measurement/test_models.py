"""Unit tests for Measurement model."""

import unicodedata
from types import SimpleNamespace

import pint
import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point as GEOSPoint
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import RestrictedError
from django.urls import resolve

from demo.factories import (
    ExampleMeasurementFactory,
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
)
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.models import Measurement
from fairdm.core.vocabularies import DESCRIPTION_TYPES
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    MeasurementDescriptionFactory,
    PersonFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestMeasurementLocation:
    @pytest.mark.parametrize(
        "extra",
        [
            {"location_elevation": 1.0},
            {"location_uncertainty": 1.0},
        ],
    )
    def test_the_database_refuses_elevation_or_uncertainty_without_a_location(
        self, sample, extra
    ):
        with pytest.raises(IntegrityError), transaction.atomic():
            ExampleMeasurementFactory(sample=sample, location=None, **extra)

    def test_the_database_refuses_a_negative_uncertainty(self, sample):
        with pytest.raises(IntegrityError), transaction.atomic():
            ExampleMeasurementFactory(
                sample=sample,
                location=GEOSPoint(8.4115, 49.0094, srid=4326),
                location_uncertainty=-1.0,
            )


@pytest.mark.django_db
class TestMeasurementLocalId:
    def test_the_same_local_id_is_valid_in_two_different_datasets(
        self, dataset, second_dataset, sample, second_sample
    ):
        one = ExampleMeasurementFactory(
            dataset=dataset, sample=sample, local_id="LAB-001"
        )
        two = ExampleMeasurementFactory(
            dataset=second_dataset, sample=second_sample, local_id="LAB-001"
        )

        one.full_clean()
        two.full_clean()
        assert one.local_id == two.local_id == "LAB-001"


@pytest.mark.django_db
class TestMeasurementVocabularyValidation:
    """The guard is one mixin shared by description, date and identifier, so one type is tested."""

    def test_a_type_outside_the_vocabulary_is_refused_by_full_clean(self, measurement):
        description = MeasurementDescriptionFactory.build(
            related=measurement, type=f"{DESCRIPTION_TYPES}/not-a-real-description-type"
        )
        with pytest.raises(ValidationError) as exc_info:
            description.full_clean()
        assert "not-a-real-description-type" in str(exc_info.value)

    def test_a_type_outside_the_vocabulary_is_refused_on_direct_save(self, measurement):
        with pytest.raises(ValidationError) as exc_info:
            MeasurementDescriptionFactory(
                related=measurement,
                type=f"{DESCRIPTION_TYPES}/not-a-real-description-type",
            )
        assert "not-a-real-description-type" in str(exc_info.value)


@pytest.mark.django_db
class TestMeasurementCrossDatasetSampleLinking:
    def test_a_measurement_may_sit_in_a_different_dataset_from_its_sample(
        self, sample, second_dataset
    ):
        measurement = ExampleMeasurementFactory(sample=sample, dataset=second_dataset)

        measurement.full_clean()

        assert measurement.dataset != measurement.sample.dataset


@pytest.mark.django_db
class TestMeasurementDirectInstantiation:
    def test_measurement_cannot_be_instantiated_directly(self, sample):
        measurement = Measurement(
            name="Direct Measurement",
            sample=sample,
            dataset=sample.dataset,
        )

        with pytest.raises(ValidationError):
            measurement.clean()


@pytest.mark.django_db
class TestMeasurementURLPattern:
    def test_get_absolute_url_resolves_to_the_measurement_overview(self, measurement):
        match = resolve(measurement.get_absolute_url())

        assert match.view_name == "measurement:overview"
        assert match.kwargs["uuid"] == str(measurement.uuid)


@pytest.mark.django_db
class TestMeasurementDeletion:
    def test_deleting_a_sample_is_refused_while_a_measurement_refers_to_it(
        self, measurement
    ):
        with pytest.raises(RestrictedError):
            measurement.sample.delete()

        assert Measurement.objects.filter(pk=measurement.pk).exists()

    def test_deleting_the_sample_dataset_is_refused_while_a_measurement_elsewhere_refers_to_it(
        self, measurement, second_dataset
    ):
        measurement.dataset = second_dataset
        measurement.save()

        with pytest.raises(RestrictedError):
            measurement.sample.dataset.delete()

        assert Measurement.objects.filter(pk=measurement.pk).exists()


@pytest.mark.django_db
class TestGetValue:
    def test_type_nominating_a_value_reports_that_value(self, sample):
        measurement = ICP_MS_MeasurementFactory(sample=sample, value="5.000")
        measurement.refresh_from_db()

        assert measurement.get_value() == measurement.value

    def test_type_nominating_none_reports_the_record_name(self, sample):
        measurement = ExampleMeasurementFactory(sample=sample, name="Base Reading")

        assert measurement.get_value() == "Base Reading"

    def test_a_negative_uncertainty_leaves_the_plain_value(self, sample):
        stored = ICP_MS_MeasurementFactory(
            sample=sample, value="120.5", uncertainty="-2.5"
        )
        measurement = type(stored).objects.get(pk=stored.pk)

        assert measurement.get_value() == measurement.value
        assert measurement.print_value() == str(measurement.value)
        assert str(measurement) == str(measurement.value)

    def test_an_uncertainty_in_units_the_value_cannot_take_leaves_the_plain_value(self):
        units = pint.get_application_registry()
        measurement = ICP_MS_MeasurementFactory.build(
            value=units.Quantity(120.5, "meter"),
            uncertainty=units.Quantity(2, "second"),
        )

        assert measurement.get_value() == measurement.value

    def test_a_measurement_with_no_value_is_named_by_its_name(self, sample):
        measurement = ICP_MS_MeasurementFactory(
            sample=sample, name="206Pb/238U, spot 3", value=None
        )
        assert str(measurement) == "206Pb/238U, spot 3"

    def test_a_measurement_with_no_value_or_name_is_named_by_its_portal_id(
        self, sample
    ):
        measurement = ICP_MS_MeasurementFactory(sample=sample, name="", value=None)
        assert str(measurement) == measurement.uuid


@pytest.mark.django_db
class TestGetValueWithUncertainty:
    def test_uncertainty_is_carried_with_the_value(self, sample):
        measurement = ICP_MS_MeasurementFactory(
            sample=sample, value="5.000", uncertainty="0.300"
        )
        measurement.refresh_from_db()

        result = measurement.get_value()

        # A pint `Measurement`'s attributes are `.value` and `.error`, not `.err`.
        assert isinstance(result, pint.Measurement)
        assert result.value.magnitude == pytest.approx(
            float(measurement.value.magnitude)
        )
        assert result.error.magnitude == pytest.approx(
            float(measurement.uncertainty.magnitude)
        )
        assert result.value.units == measurement.value.units


class TestGetValuePlainNumber:
    def test_plain_number_with_uncertainty_present_is_returned_unchanged(self):
        record = SimpleNamespace(name="Plain Reading", value=42, uncertainty=5)

        assert Measurement.get_value(record) == 42

    def test_plain_number_with_no_uncertainty_is_returned_unchanged(self):
        record = SimpleNamespace(name="Plain Reading", value=42)

        assert Measurement.get_value(record) == 42


@pytest.mark.django_db
class TestPrintValue:
    def test_a_type_nominating_no_value_prints_the_record_name(self, sample):
        measurement = ExampleMeasurementFactory(sample=sample, name="Base Reading")

        assert measurement.print_value() == "Base Reading"

    def test_renders_value_uncertainty_and_units_together(self, sample):
        measurement = ICP_MS_MeasurementFactory(
            sample=sample, value="5.000", uncertainty="0.300"
        )
        measurement.refresh_from_db()

        # NFKC-normalised: the unit registry is free to render the micro prefix as
        # either U+00B5 MICRO SIGN or U+03BC GREEK SMALL LETTER MU (both normalise to
        # the same codepoint), and that choice belongs to the registry, not this test.
        assert unicodedata.normalize(
            "NFKC", measurement.print_value()
        ) == unicodedata.normalize("NFKC", "5.00 ± 0.30 µg/l")


@pytest.mark.django_db
class TestMoveKeepsManager:
    def refusal_code(self, measurement):
        with pytest.raises(ValidationError) as refused:
            measurement.clean()
        return refused.value.error_dict["dataset"][0].code

    def test_a_move_to_a_dataset_that_gives_no_manager_is_refused(self, make_manager):
        dataset = DatasetFactory()
        make_manager(dataset)
        measurement = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )
        measurement.dataset = DatasetFactory(project=dataset.project)

        assert self.refusal_code(measurement) == "no_manager"

    def test_a_move_to_a_dataset_with_a_manager_passes(self, make_manager):
        dataset, other = DatasetFactory(), DatasetFactory()
        make_manager(dataset)
        make_manager(other)
        measurement = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )
        measurement.dataset = other

        measurement.clean()

    def test_a_move_keeps_a_manager_listed_on_the_measurement(self, make_manager):
        dataset = DatasetFactory()
        measurement = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )
        make_manager(measurement)
        measurement.dataset = DatasetFactory()

        measurement.clean()

    def test_the_samples_dataset_does_not_hold_a_measurement_up(self, make_manager):
        dataset = DatasetFactory()
        make_manager(dataset)
        measurement = ExampleMeasurementFactory(
            dataset=DatasetFactory(), sample=RockSampleFactory(dataset=dataset)
        )
        measurement.dataset = DatasetFactory()

        measurement.clean()

    def test_a_measurement_that_had_no_manager_may_move_anywhere(self):
        dataset = DatasetFactory()
        measurement = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )
        measurement.dataset = DatasetFactory()

        measurement.clean()

    def test_a_measurement_whose_dataset_did_not_change_passes(self, make_manager):
        dataset = DatasetFactory()
        make_manager(dataset)
        measurement = ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )

        measurement.clean()


@pytest.mark.django_db
class TestMeasurementEffectiveLocation:
    """FR-013 and FR-014: own location first, the sample's only for a viewer who may open it."""

    @pytest.fixture
    def released(self):
        return DatasetFactory(visibility=Visibility.PUBLIC, published=True)

    @pytest.fixture
    def hidden(self):
        return DatasetFactory(visibility=Visibility.PRIVATE, published=False)

    def test_the_own_location_wins_with_its_elevation_and_uncertainty(self, released):
        sample = RockSampleFactory(
            dataset=released, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        measurement = ExampleMeasurementFactory(
            sample=sample,
            dataset=released,
            location=GEOSPoint(8.4318, 49.09495, srid=4326),
            location_elevation=112.0,
            location_uncertainty=25.0,
        )

        point, elevation, uncertainty, source = measurement.effective_location_for(None)

        assert (point.x, point.y) == (8.4318, 49.09495)
        assert (elevation, uncertainty, source) == (112.0, 25.0, "own")

    def test_the_sample_is_used_when_the_measurement_has_none(self, released):
        sample = RockSampleFactory(
            dataset=released,
            location=GEOSPoint(12.5, 41.5, srid=4326),
            location_elevation=40.0,
            location_uncertainty=3.0,
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)

        point, elevation, uncertainty, source = measurement.effective_location_for(None)

        assert (point.x, point.y) == (12.5, 41.5)
        assert (elevation, uncertainty, source) == (40.0, 3.0, "sample")

    def test_neither_having_a_location_gives_none(self, released):
        sample = RockSampleFactory(dataset=released)
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)

        assert measurement.effective_location_for(None) is None

    def test_a_visitor_gets_none_for_a_sample_they_may_not_open(self, released, hidden):
        sample = RockSampleFactory(
            dataset=hidden, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)

        assert measurement.effective_location_for(None) is None
        assert measurement.effective_location_for(AnonymousUser()) is None

    def test_a_person_who_may_open_the_sample_gets_its_location(self, released, hidden):
        sample = RockSampleFactory(
            dataset=hidden, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)
        member = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=hidden, contributor=member, level=ContributionLevel.VIEW
        )

        found = measurement.effective_location_for(member)

        assert found.source == "sample"
        assert (found.point.x, found.point.y) == (12.5, 41.5)

    def test_a_person_with_no_level_on_the_sample_gets_none(self, released, hidden):
        sample = RockSampleFactory(
            dataset=hidden, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)

        assert measurement.effective_location_for(PersonFactory(is_active=True)) is None

    def test_changing_the_samples_location_leaves_the_measurements_own(self, released):
        sample = RockSampleFactory(
            dataset=released, location=GEOSPoint(12.5, 41.5, srid=4326)
        )
        measurement = ExampleMeasurementFactory(
            sample=sample,
            dataset=released,
            location=GEOSPoint(8.4318, 49.09495, srid=4326),
        )

        sample.location = GEOSPoint(1.0, 2.0, srid=4326)
        sample.save()

        stored = Measurement.objects.get(pk=measurement.pk)
        assert (stored.location.x, stored.location.y) == (8.4318, 49.09495)
        assert stored.effective_location_for(None).source == "own"
