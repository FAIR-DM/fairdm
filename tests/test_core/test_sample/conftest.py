"""
Test fixtures for Sample model tests.

Provides reusable fixtures for testing the Sample model and related functionality.
"""

import pytest
from django.contrib.auth import get_user_model

from fairdm.factories import DatasetFactory, PersonFactory, ProjectFactory
from fairdm.registry import registry

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
    """Create a test dataset linked to a project."""
    return DatasetFactory(project=project)


@pytest.fixture
def rock_sample(db, dataset):
    """Create a test RockSample (polymorphic subclass)."""
    from fairdm_demo.models import RockSample

    return RockSample.objects.create(
        name="Test Rock",
        dataset=dataset,
        rock_type="igneous",
        collection_date="2024-01-15",
    )


@pytest.fixture
def water_sample(db, dataset):
    """Create a test WaterSample (polymorphic subclass)."""
    from fairdm_demo.models import WaterSample

    return WaterSample.objects.create(
        name="Test Water",
        dataset=dataset,
        water_source="river",
        ph_level=7.2,
        temperature_celsius=20.5,
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
