"""Test fixtures for Measurement model tests."""

import pytest
from django.contrib.auth import get_user_model

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.measurement.models import (
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.registry import registry

User = get_user_model()


@pytest.fixture
def user(db):
    return PersonFactory()


@pytest.fixture
def project(db):
    return ProjectFactory()


@pytest.fixture
def dataset(db, project):
    return DatasetFactory(project=project)


@pytest.fixture
def sample(db, dataset):
    return RockSampleFactory(dataset=dataset)


@pytest.fixture
def second_dataset(db, project):
    return DatasetFactory(project=project)


@pytest.fixture
def second_sample(db, second_dataset):
    return RockSampleFactory(dataset=second_dataset)


@pytest.fixture
def user_no_rights(db):
    return PersonFactory(is_active=True)


@pytest.fixture
def measurement(db, sample):
    return ExampleMeasurementFactory(sample=sample)


@pytest.fixture
def example_measurement(db, sample):
    from demo.models import ExampleMeasurement

    return ExampleMeasurement.objects.create(
        name="Test Measurement",
        sample=sample,
        dataset=sample.dataset,
        char_field="Example text",
        integer_field=42,
    )


@pytest.fixture
def xrf_measurement(db, sample):
    from demo.models import XRFMeasurement

    return XRFMeasurement.objects.create(
        name="XRF Analysis",
        sample=sample,
        dataset=sample.dataset,
        element="Si",
        concentration_ppm=250000.0,
        detection_limit_ppm=5.0,
    )


@pytest.fixture
def icp_ms_measurement(db, sample):
    from demo.models import ICP_MS_Measurement

    return ICP_MS_Measurement.objects.create(
        name="ICP-MS Analysis",
        sample=sample,
        dataset=sample.dataset,
        isotope="207Pb",
        counts_per_second=15000.0,
        concentration_ppb=120.5,
    )


@pytest.fixture
def clean_registry():
    original_registry = registry._registry.copy()

    yield

    registry._registry = original_registry


@pytest.fixture
def build_measurements_with_related():
    def build(dataset, count):
        """Create `count` measurements in `dataset`, each with a sample and a contributor."""
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

    return build


@pytest.fixture
def build_measurements_with_metadata():
    def build(dataset, count):
        """Create `count` measurements in `dataset`, each with a description, date and identifier."""
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

    return build
