"""
Test fixtures for Measurement model tests.

Provides reusable fixtures for testing the Measurement model and related functionality.
"""

import pytest
from django.contrib.auth import get_user_model

from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.registry import registry
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return PersonFactory()


@pytest.fixture
def project(db):
    """Create a test project."""
    return ProjectFactory()


@pytest.fixture
def dataset(db, project):
    """Create a test dataset linked to a project.

    Left at the model's own default, which is private (004-core-datasets FR-004):
    filtering measurements by a private dataset is the ordinary case, and
    `MeasurementFilter` builds its "dataset" choices from `Dataset.all_objects`
    so that it works.
    """
    return DatasetFactory(project=project)


@pytest.fixture
def sample(db, dataset):
    """Create a test sample linked to a dataset."""
    return RockSampleFactory(dataset=dataset)


@pytest.fixture
def second_dataset(db, project):
    """Create a second dataset, distinct from `dataset`, for cross-dataset cases."""
    return DatasetFactory(project=project)


@pytest.fixture
def second_sample(db, second_dataset):
    """Create a sample belonging to `second_dataset`, distinct from `sample`."""
    return RockSampleFactory(dataset=second_dataset)


@pytest.fixture
def user_no_rights(db):
    """Create a second user holding no permissions on anything at all.

    Distinct from `user`: this fixture exists specifically so a test can assert an
    absence of access without needing to reason about what `user` might have been
    granted elsewhere in the same test.
    """
    return PersonFactory(is_active=True)


@pytest.fixture
def measurement(db, sample):
    """Create a concrete measurement instance (never a bare Measurement) linked to a
    sample.

    `Measurement` is a polymorphic base that cannot be created directly (FR-011) - see
    `MeasurementFactory`'s docstring. This fixture uses the demo application's
    `ExampleMeasurementFactory` as its concrete type.
    """
    return ExampleMeasurementFactory(sample=sample)


@pytest.fixture
def example_measurement(db, sample):
    """Create a test ExampleMeasurement (polymorphic subclass)."""
    from fairdm_demo.models import ExampleMeasurement

    return ExampleMeasurement.objects.create(
        name="Test Measurement",
        sample=sample,
        dataset=sample.dataset,
        char_field="Example text",
        integer_field=42,
    )


@pytest.fixture
def xrf_measurement(db, sample):
    """Create a test XRFMeasurement (polymorphic subclass)."""
    from fairdm_demo.models import XRFMeasurement

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
    """Create a test ICP-MS Measurement (polymorphic subclass)."""
    from fairdm_demo.models import ICP_MS_Measurement

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
    """Clean the registry before and after each test.

    This ensures tests don't interfere with each other by leaving
    registered models in the registry.
    """
    # Store original state
    original_registry = registry._registry.copy()

    yield

    # Restore original state
    registry._registry = original_registry
