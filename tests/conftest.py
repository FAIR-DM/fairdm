"""Root-level pytest configuration for FairDM tests."""

import contextlib
from importlib import import_module, reload

import pytest
from django.conf import settings
from django.core.management import call_command
from django.urls import clear_url_caches

from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # Seed the recommended licences through the real deployment path
        # (`fairdm/management/commands/seed_licenses.py`), the route a portal takes.
        call_command("seed_licenses", verbosity=0)
        from research_vocabs.models import Concept

        Concept.preload()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def project(user):
    return ProjectFactory(owner=user)


@pytest.fixture
def disconnect_shipped_role_guard():
    # The guard refuses to delete or rename a shipped role, bulk deletes included. Tests that need
    # a shipped role missing switch it off.
    from django.contrib.auth.models import Group
    from django.db.models.signals import pre_delete, pre_save

    from fairdm.contrib.contributors.receivers import (
        refuse_shipped_role_deletion,
        refuse_shipped_role_rename,
    )

    pre_delete.disconnect(
        refuse_shipped_role_deletion,
        sender=Group,
        dispatch_uid="contributors.refuse_shipped_role_deletion",
    )
    pre_save.disconnect(
        refuse_shipped_role_rename,
        sender=Group,
        dispatch_uid="contributors.refuse_shipped_role_rename",
    )
    try:
        yield
    finally:
        pre_delete.connect(
            refuse_shipped_role_deletion,
            sender=Group,
            dispatch_uid="contributors.refuse_shipped_role_deletion",
        )
        pre_save.connect(
            refuse_shipped_role_rename,
            sender=Group,
            dispatch_uid="contributors.refuse_shipped_role_rename",
        )


@pytest.fixture
def project_with_datasets():
    project = ProjectFactory()
    datasets = DatasetFactory.create_batch(3, project=project)
    return project, datasets


class PluginSandbox:
    """Declare plugins inside a test and see them served, then put everything back.

    A record type's URL patterns are built once, when its URL module is imported, so a plugin
    registered inside a test has no address until those patterns are built again. The sandbox
    saves the registry, rebuilds the patterns of every record type after each ``declare()``
    block, and on close restores the registry and rebuilds the patterns once more, so the
    plugin is gone from the registry and its address no longer resolves.

    Attributes:
        URL_MODULES: The modules that mount a record type's plugins, innermost first, then the
            modules that include them. Each is imported again so no cached resolver survives.
    """

    URL_MODULES = (
        "fairdm.core.project.urls",
        "fairdm.core.dataset.urls",
        "fairdm.core.sample.urls",
        "fairdm.core.measurement.urls",
        "fairdm.contrib.contributors.urls",
        "fairdm.contrib.location.urls",
        "fairdm.core.urls",
    )

    def __init__(self):
        from fairdm import plugins

        self.registry = plugins.registry
        self.saved = {
            model: list(entries) for model, entries in self.registry._registry.items()
        }

    @contextlib.contextmanager
    def declare(self):
        """Declare plugins in the block, then make them reachable.

        Yields:
            Nothing. Register with ``plugins.register`` inside the block.
        """
        yield
        self.rebuild()

    def rebuild(self):
        """Build every record type's URL patterns and navigation again from the registry."""
        for name in (*self.URL_MODULES, settings.ROOT_URLCONF):
            reload(import_module(name))
        clear_url_caches()

    def close(self):
        """Restore the registry and the URL configuration as they were."""
        self.registry._registry.clear()
        self.registry._registry.update(self.saved)
        self.rebuild()


@pytest.fixture
def plugin_sandbox():
    """Let a test declare plugins, serve them through the test client and leave no trace."""
    sandbox = PluginSandbox()
    try:
        yield sandbox
    finally:
        sandbox.close()
