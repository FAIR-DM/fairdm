"""
Pytest fixtures for plugin system tests.
"""

import contextlib

import pytest
from django.contrib.auth import get_user_model

from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    from fairdm.factories.contributors import UserFactory

    return UserFactory(email="test@example.com")


@pytest.fixture
def project(db):
    """Create a test project."""
    return Project.objects.create(
        name="Test Project", visibility=Project.VISIBILITY.PUBLIC, status=Project.STATUS_CHOICES.IN_PROGRESS
    )


@pytest.fixture
def dataset(db, project):
    """Create a test dataset."""
    return Dataset.objects.create(name="Test Dataset", project=project)


@pytest.fixture
def sample(db, dataset):
    """Create a test sample."""
    return Sample.objects.create(dataset=dataset, local_id="TEST-001")


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    from fairdm.factories.contributors import UserFactory

    return UserFactory(email="admin@example.com", is_staff=True, is_superuser=True)


@pytest.fixture
def clear_registry():
    """Clear plugin registry between tests to prevent pollution.

    Use this fixture explicitly in tests that register plugins dynamically
    to ensure a clean state. Don't use autouse=True as it will break tests
    that expect real plugins to be registered (like test_project_edit_plugin.py).

    After clearing, this fixture re-imports all plugin modules to restore
    the registry state for subsequent tests.
    """
    import sys
    from importlib import import_module, reload

    from fairdm import plugins

    # Clear the registry before the test
    plugins.registry._registry.clear()
    yield
    # Clear again after test
    plugins.registry._registry.clear()

    # Re-import plugin modules to restore registry state
    # Get all plugin modules that were previously imported
    plugin_modules = [name for name in sys.modules if name.endswith(".plugins")]

    # Reload each plugin module to re-execute @register decorators
    for module_name in plugin_modules:
        if module_name in sys.modules:
            try:
                reload(sys.modules[module_name])
            except Exception:
                # If reload fails, try reimporting (skip if both fail)
                with contextlib.suppress(Exception):
                    import_module(module_name)


@pytest.fixture
def authenticated_client(client, user):
    """Return a client with an authenticated user."""
    client.force_login(user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Return a client with an authenticated admin user."""
    client.force_login(admin_user)
    return client
