"""
Pytest fixtures for composed test scenarios.

This module provides pytest fixtures that compose multiple factories
into reusable test scenarios.

Usage:
    @pytest.mark.django_db
    def test_something(project_with_datasets):
        project, datasets = project_with_datasets
        assert project.datasets.count() == 3

See Also:
    - fairdm/core/factories.py for factory-boy factory declarations
    - fairdm/factories.py for convenient factory imports
    - docs/contributing/testing/fixtures.md
"""

import pytest

from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory


@pytest.fixture
def user():
    """
    Create a test user.

    Returns:
        User: A user instance with default values
    """
    return UserFactory()


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
