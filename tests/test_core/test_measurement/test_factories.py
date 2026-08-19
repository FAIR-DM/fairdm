"""Tests for measurement factories.

Covers the metadata factories declared in ``fairdm/factories/core.py``
(``MeasurementDescriptionFactory``, ``MeasurementDateFactory``,
``MeasurementIdentifierFactory``), the abstract ``MeasurementFactory`` base, the
concrete demo measurement factories in ``fairdm_demo/factories.py``, and their
exports from ``fairdm.factories``.
"""

import pytest

from fairdm.core.measurement.models import (
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.factories.core import (
    MeasurementDateFactory,
    MeasurementDescriptionFactory,
    MeasurementIdentifierFactory,
)
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory


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
