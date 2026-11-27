"""Tests for measurement factories."""

import factory
import pytest

from demo.factories import ExampleMeasurementFactory
from fairdm.core.measurement.models import MeasurementIdentifier
from fairdm.factories.core import MeasurementFactory, MeasurementIdentifierFactory


@pytest.mark.django_db
class TestMeasurementIdentifierFactory:
    def test_identifier_values_are_unique_across_instances(
        self, measurement, second_sample
    ):
        first = MeasurementIdentifierFactory(related=measurement)
        second = MeasurementIdentifierFactory(
            related=ExampleMeasurementFactory(sample=second_sample)
        )

        assert first.value != second.value
        assert MeasurementIdentifier.objects.count() == 2


@pytest.mark.django_db
class TestMeasurementFactoryIsAbstract:
    def test_calling_it_directly_refuses(self, sample):
        with pytest.raises(factory.errors.FactoryError):
            MeasurementFactory(sample=sample)


class TestFairdmFactoriesExports:
    def test_measurement_factories_appear_in_all(self):
        import fairdm.factories as factories_module

        for name in (
            "MeasurementDateFactory",
            "MeasurementDescriptionFactory",
            "MeasurementFactory",
            "MeasurementIdentifierFactory",
        ):
            assert name in factories_module.__all__
