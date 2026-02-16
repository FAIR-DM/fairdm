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
        # Load Creative Commons licenses from django-content-license
        call_command("loaddata", "creativecommons", verbosity=0)


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
