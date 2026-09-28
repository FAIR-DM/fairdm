"""Factories for the models defined in tests/registry_models."""

import factory
from factory.django import DjangoModelFactory

from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


class ConcreteSampleFactory(DjangoModelFactory):
    """Build a ConcreteSample. Vary it by overriding fields at the call site."""

    class Meta:
        model = ConcreteSample

    name = factory.Sequence(lambda n: f"concrete-sample-{n}")


class ConcreteMeasurementFactory(DjangoModelFactory):
    """Build a ConcreteMeasurement."""

    class Meta:
        model = ConcreteMeasurement

    reading = factory.Sequence(lambda n: float(n))
