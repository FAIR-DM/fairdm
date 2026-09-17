"""
Root-level pytest configuration for FairDM tests.

This conftest.py provides session-level fixtures and configuration that apply
to all tests across all test layers (unit, integration, contract).
"""

import pytest
from django.core.management import call_command

from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Session-level database setup.

    Creates test database once per test session and loads required
    reference data that all tests can use.

    The django_db_blocker ensures database access is properly controlled.
    """
    with django_db_blocker.unblock():
        # Seed the licences FairDM recommends, through the real deployment
        # path (`fairdm/management/commands/seed_licenses.py`) rather than
        # loading django-content-license's fixture by hand - so the test
        # suite exercises the same route a portal does (FR-007a, T099).
        call_command("seed_licenses", verbosity=0)
        # Load all registered research vocabularies (e.g. FairDM Roles)
        from research_vocabs.models import Concept

        Concept.preload()


@pytest.fixture
def user():
    """
    Create a test user.

    Returns:
        User: A user instance with default values
    """
    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    """
    Create an authenticated client for testing views that require login.

    Args:
        client: The Django test client fixture
        user: The user fixture to authenticate
    Returns:
        Client: An authenticated test client instance
    """
    client.force_login(user)
    return client


@pytest.fixture
def project(user):
    """
    Create a project with a test user as owner.

    Returns:
        Project: A project instance owned by a test user
    """
    return ProjectFactory(owner=user)


@pytest.fixture
def disconnect_shipped_role_guard():
    """Disconnect T021's `Group` `pre_delete`/`pre_save` guard for the duration of
    a test.

    The guard refuses to delete or rename a shipped portal role through the ORM
    (`fairdm/contrib/contributors/receivers.py`), including a bulk
    `Group.objects.all().delete()` - correctly, since nothing in a portal may
    bulk-delete a shipped role. A handful of tests need a shipped role to be
    *missing* to prove `PortalRoles.reconcile()` / `migrate` rebuilds it from
    nothing, and the specification's own account of how a role can actually go
    missing is exactly this: from outside the ORM, restored on the next
    `migrate` (D23). This fixture models that route explicitly, by name, only
    for the tests that request it - never weaken the guard itself to reach the
    same effect, and `TestProtection` must never request this fixture, since its
    whole purpose is proving the guard holds.
    """
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
    """
    Create a project with 3 datasets.

    Returns:
        tuple: (project, [dataset1, dataset2, dataset3])

    Usage:
        @pytest.mark.django_db
        def test_something(project_with_datasets):
            project, datasets = project_with_datasets
            assert len(datasets) == 3
            assert all(d.project == project for d in datasets)
    """
    project = ProjectFactory()
    datasets = DatasetFactory.create_batch(3, project=project)
    return project, datasets
