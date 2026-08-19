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
