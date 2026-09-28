"""Shared fixtures for Project tests."""

import pytest
from guardian.shortcuts import assign_perm

from fairdm.factories import ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def public_project(db):
    return ProjectFactory(visibility=Visibility.PUBLIC)


@pytest.fixture
def private_project(db):
    return ProjectFactory(visibility=Visibility.PRIVATE)


@pytest.fixture
def user_with_change_permission(db):
    user = UserFactory()
    user.project = ProjectFactory()
    # Editing rights without view is a state no grant path produces: registering gives
    # all five.
    assign_perm("view_project", user, user.project)
    assign_perm("change_project", user, user.project)
    return user


@pytest.fixture
def user_with_delete_permission(db):
    user = UserFactory()
    user.project = ProjectFactory()
    assign_perm("view_project", user, user.project)
    assign_perm("delete_project", user, user.project)
    return user


@pytest.fixture
def user_with_no_permission(db):
    user = UserFactory()
    user.project = ProjectFactory()
    return user
