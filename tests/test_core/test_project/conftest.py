"""Shared fixtures for Project tests.

Thin wrappers over the factories in ``fairdm.factories``, per constitution
Article X.
"""

import pytest
from guardian.shortcuts import assign_perm

from fairdm.factories import ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def public_project(db):
    """A project with PUBLIC visibility."""
    return ProjectFactory(visibility=Visibility.PUBLIC)


@pytest.fixture
def private_project(db):
    """A project with PRIVATE visibility."""
    return ProjectFactory(visibility=Visibility.PRIVATE)


@pytest.fixture
def user_with_change_permission(db):
    """A user holding ``change_project`` on a project of their own, and
    nothing else.

    The project is carried on the returned user as ``.project`` - an
    in-memory attribute only, never persisted - so a test can assert the
    grant without also depending on one of the fixtures above.
    """
    user = UserFactory()
    user.project = ProjectFactory()
    assign_perm("change_project", user, user.project)
    return user


@pytest.fixture
def user_with_delete_permission(db):
    """A user holding ``delete_project`` on a project of their own, and
    nothing else. See ``user_with_change_permission`` for ``.project``."""
    user = UserFactory()
    user.project = ProjectFactory()
    assign_perm("delete_project", user, user.project)
    return user


@pytest.fixture
def user_with_no_permission(db):
    """A user holding neither ``change_project`` nor ``delete_project`` on
    any project. See ``user_with_change_permission`` for ``.project``."""
    user = UserFactory()
    user.project = ProjectFactory()
    return user
