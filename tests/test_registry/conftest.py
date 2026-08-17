"""
Pytest fixtures for registry tests.

This conftest.py provides fixtures that ensure clean state between tests
when working with Django models and the FairDM registry.
"""

import uuid

import factory
import pytest
from django.apps import apps
from django.contrib import admin
from factory.django import DjangoModelFactory

from fairdm.registry import registry
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


class ConcreteSampleFactory(DjangoModelFactory):
    """The one factory for ConcreteSample. Vary it by overriding at the call site."""

    class Meta:
        model = ConcreteSample

    name = factory.Sequence(lambda n: f"concrete-sample-{n}")


class ConcreteMeasurementFactory(DjangoModelFactory):
    """The one factory for ConcreteMeasurement."""

    class Meta:
        model = ConcreteMeasurement

    reading = factory.Sequence(lambda n: float(n))


@pytest.fixture
def concrete_sample():
    """The concrete Sample subclass tests register."""
    return ConcreteSample


@pytest.fixture
def concrete_measurement():
    """The concrete Measurement subclass tests register."""
    return ConcreteMeasurement


@pytest.fixture
def sample_instance(db):
    """One saved ConcreteSample. A variation needs no fixture, call the factory."""
    return ConcreteSampleFactory()


@pytest.fixture
def measurement_instance(db):
    """One saved ConcreteMeasurement."""
    return ConcreteMeasurementFactory()


@pytest.fixture
def clean_registry():
    """An empty registry for the test, with global state put back afterwards.

    Restoring rather than clearing matters: the registry is global state populated
    once at app load, so a test that empties it and walks away breaks every later
    test that expects the demo models to be registered.

    The Django admin site is restored too. Registering a model registers its admin
    class, and admin registration failures now propagate rather than being
    swallowed, so a model left in `admin.site` by one test surfaces in the next as
    an admin page that cannot resolve an app label for a test-only model.
    """
    saved = dict(registry._registry)
    saved_locations = dict(registry._locations)
    saved_admin = dict(admin.site._registry)

    registry._registry.clear()
    registry._locations.clear()

    yield registry

    registry._registry.clear()
    registry._registry.update(saved)
    registry._locations.clear()
    registry._locations.update(saved_locations)
    admin.site._registry.clear()
    admin.site._registry.update(saved_admin)


@pytest.fixture
def unique_app_label():
    """
    Generate a unique app label for test models.

    This prevents Django model registry conflicts when creating
    models dynamically in tests. Each test gets a unique app label.

    Example usage:
        def test_something(unique_app_label):
            class TestSample(Sample):
                class Meta:
                    app_label = unique_app_label

    Returns:
        str: A unique app label like "test_app_abc123def456"
    """
    return f"test_app_{uuid.uuid4().hex[:12]}"


@pytest.fixture(autouse=True)
def cleanup_test_app_models():
    """
    Automatically clean up test models from Django's app registry after each test.

    This fixture runs automatically for all registry tests (autouse=True).
    It removes any models registered under app labels starting with 'test_app'
    to prevent conflicts between tests.

    Note: This is a workaround for dynamically created models in tests.
    Django's app registry is not designed to have models unregistered.
    """
    yield

    # After test completes, clean up test models
    test_apps = [label for label in apps.all_models if label.startswith("test_app")]

    for app_label in test_apps:
        # Remove all models for this test app
        if app_label in apps.all_models:
            apps.all_models[app_label].clear()
