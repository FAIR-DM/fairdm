"""Root-level pytest configuration for FairDM tests."""

import pytest
from django.core.management import call_command

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
