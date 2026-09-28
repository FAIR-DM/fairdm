"""Pytest fixtures for registry tests."""

import pytest
from django.apps import apps
from django.contrib import admin

from fairdm.registry import registry
from tests.factories import ConcreteMeasurementFactory, ConcreteSampleFactory
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


@pytest.fixture
def concrete_sample():
    return ConcreteSample


@pytest.fixture
def concrete_measurement():
    return ConcreteMeasurement


@pytest.fixture
def sample_instance(db):
    return ConcreteSampleFactory()


@pytest.fixture
def measurement_instance(db):
    return ConcreteMeasurementFactory()


@pytest.fixture
def clean_registry():
    # Restore rather than clear: a test that empties the global registry breaks every later test
    # that expects the demo models. The admin site is restored for the same reason.
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


@pytest.fixture(autouse=True)
def cleanup_test_app_models():
    # Django cannot unregister models, so clear those registered under test_app labels.
    yield

    test_apps = [label for label in apps.all_models if label.startswith("test_app")]

    for app_label in test_apps:
        if app_label in apps.all_models:
            apps.all_models[app_label].clear()
