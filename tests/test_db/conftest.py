"""Fixtures for the model field tests."""

import pytest

from fairdm.factories import DatasetFactory
from tests.factories import ConcreteMeasurementFactory, ConcreteSampleFactory


@pytest.fixture
def measurement(db):
    """Return a saved measurement whose ``depth`` quantity is empty."""
    dataset = DatasetFactory()
    return ConcreteMeasurementFactory(
        dataset=dataset, sample=ConcreteSampleFactory(dataset=dataset)
    )
