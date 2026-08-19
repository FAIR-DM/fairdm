"""Tests for measurement factories.

Covers the metadata factories declared in ``fairdm/factories/core.py``
(``MeasurementDescriptionFactory``, ``MeasurementDateFactory``,
``MeasurementIdentifierFactory``), the abstract ``MeasurementFactory`` base, the
concrete demo measurement factories in ``fairdm_demo/factories.py``, and their
exports from ``fairdm.factories``.
"""

import factory
import pytest

from fairdm.core.measurement.models import (
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.core.models import Measurement
from fairdm.factories.core import (
    MeasurementDateFactory,
    MeasurementDescriptionFactory,
    MeasurementFactory,
    MeasurementIdentifierFactory,
)
from fairdm_demo.factories import (
    ExampleMeasurementFactory,
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    XRFMeasurementFactory,
)
from fairdm_demo.models import ICP_MS_Measurement, XRFMeasurement


@pytest.mark.django_db
class TestMeasurementDescriptionFactory:
    """T001 - MeasurementDescriptionFactory defaults to a real vocabulary member."""

    def test_default_type_is_a_measurement_description_vocabulary_member(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        description = MeasurementDescriptionFactory(related=measurement)

        assert description.type in {
            "MeasurementConditions",
            "MeasurementSetup",
            "MeasurementTearDown",
            "Other",
        }

    def test_two_descriptions_of_different_types_do_not_collide(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        first = MeasurementDescriptionFactory(
            related=measurement, type="MeasurementSetup"
        )
        second = MeasurementDescriptionFactory(
            related=measurement, type="MeasurementTearDown"
        )

        assert MeasurementDescription.objects.filter(related=measurement).count() == 2
        assert first.type != second.type


@pytest.mark.django_db
class TestMeasurementDateFactory:
    """T001 - MeasurementDateFactory defaults to a real vocabulary member."""

    def test_default_type_is_a_measurement_date_vocabulary_member(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        date = MeasurementDateFactory(related=measurement)

        assert date.type in {"Setup", "TearDown"}

    def test_two_dates_of_different_types_do_not_collide(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        first = MeasurementDateFactory(related=measurement, type="Setup")
        second = MeasurementDateFactory(related=measurement, type="TearDown")

        assert MeasurementDate.objects.filter(related=measurement).count() == 2
        assert first.type != second.type


@pytest.mark.django_db
class TestMeasurementIdentifierFactory:
    """T001 - MeasurementIdentifierFactory defaults to a real vocabulary member."""

    def test_default_type_is_a_measurement_identifier_vocabulary_member(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        identifier = MeasurementIdentifierFactory(related=measurement)

        assert identifier.type in {"DOI"}

    def test_identifier_values_are_unique_across_instances(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        first = MeasurementIdentifierFactory(related=measurement)
        second = MeasurementIdentifierFactory(
            related=ExampleMeasurementFactory(sample=RockSampleFactory())
        )

        assert first.value != second.value
        assert MeasurementIdentifier.objects.filter(related=measurement).count() == 1


@pytest.mark.django_db
class TestMeasurementFactoryIsAbstract:
    """T002 - MeasurementFactory refuses direct use; the bare Measurement record is
    what FR-011 forbids."""

    def test_calling_it_directly_refuses(self):
        with pytest.raises(factory.errors.FactoryError):
            MeasurementFactory(sample=RockSampleFactory())


@pytest.mark.django_db
class TestConcreteMeasurementFactories:
    """T003 - each demo measurement type's factory produces a valid instance of that
    type, with its own required fields supplied, given no arguments beyond a sample."""

    def test_example_measurement_factory_produces_an_example_measurement(self):
        from fairdm_demo.models import ExampleMeasurement

        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert isinstance(measurement, ExampleMeasurement)
        assert measurement.pk is not None

    def test_xrf_measurement_factory_supplies_its_required_fields(self):
        measurement = XRFMeasurementFactory(sample=RockSampleFactory())

        assert isinstance(measurement, XRFMeasurement)
        assert measurement.pk is not None
        assert measurement.element
        assert measurement.concentration_ppm is not None

    def test_icp_ms_measurement_factory_supplies_its_required_fields(self):
        measurement = ICP_MS_MeasurementFactory(sample=RockSampleFactory())

        assert isinstance(measurement, ICP_MS_Measurement)
        assert measurement.pk is not None
        assert measurement.isotope
        assert measurement.counts_per_second is not None


class TestFairdmFactoriesExports:
    """T004 - every measurement factory declared in fairdm/factories/core.py is
    importable from fairdm.factories and appears in __all__."""

    def test_measurement_factories_are_importable_from_the_package(self):
        from fairdm.factories import (
            MeasurementDateFactory,
            MeasurementDescriptionFactory,
            MeasurementFactory,
            MeasurementIdentifierFactory,
        )

        assert MeasurementDateFactory is not None
        assert MeasurementDescriptionFactory is not None
        assert MeasurementFactory is not None
        assert MeasurementIdentifierFactory is not None

    def test_measurement_factories_appear_in_all(self):
        import fairdm.factories as factories_module

        for name in (
            "MeasurementDateFactory",
            "MeasurementDescriptionFactory",
            "MeasurementFactory",
            "MeasurementIdentifierFactory",
        ):
            assert name in factories_module.__all__


@pytest.mark.django_db
class TestMeasurementFixtures:
    """T005 - the measurement fixture yields a concrete measurement type, never a bare
    Measurement, and fixtures exist for a second dataset with its own sample, and for a
    user holding no rights at all."""

    def test_measurement_fixture_yields_a_concrete_type_not_a_bare_measurement(
        self, measurement
    ):
        assert type(measurement) is not Measurement
        assert isinstance(measurement, Measurement)

    def test_second_dataset_fixture_has_its_own_sample(
        self, dataset, second_dataset, second_sample
    ):
        assert second_dataset != dataset
        assert second_sample.dataset == second_dataset

    def test_user_no_rights_fixture_holds_no_rights(self, measurement, user_no_rights):
        assert not user_no_rights.has_perm(
            "measurement.view_measurement", measurement
        )
        assert not user_no_rights.has_perm(
            "measurement.change_measurement", measurement
        )
        assert not user_no_rights.has_perm(
            "measurement.delete_measurement", measurement
        )
