"""
Pytest fixtures for registry tests.

This conftest.py provides fixtures that ensure clean state between tests
when working with Django models and the FairDM registry.
"""

import uuid

import pytest
from django.apps import apps

from fairdm.registry import registry


@pytest.fixture
def clean_registry():
    """
    Clean the FairDM registry before and after each test.
    
    This fixture:
    - Clears any previously registered models
    - Yields the clean registry for the test
    - Clears the registry after the test completes
    
    Use this fixture when tests register models to avoid conflicts.
    """
    # Clear registry before test
    registry._registry.clear()

    yield registry

    # Clear registry after test
    registry._registry.clear()


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
    test_apps = [label for label in apps.all_models.keys() if label.startswith("test_app")]
    
    for app_label in test_apps:
        # Remove all models for this test app
        if app_label in apps.all_models:
            apps.all_models[app_label].clear()

