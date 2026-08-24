"""Tests for the project test package's shared fixtures (T005).

Source: ``tests/test_core/test_project/conftest.py``

Each fixture is asserted against what it claims to yield, not merely that a
record was created.
"""

import pytest

from fairdm.core.project.models import Project
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectFixtures:
    def test_public_project_is_publicly_visible(self, public_project):
        assert isinstance(public_project, Project)
        assert public_project.visibility == Visibility.PUBLIC

    def test_private_project_is_privately_visible(self, private_project):
        assert isinstance(private_project, Project)
        assert private_project.visibility == Visibility.PRIVATE

    def test_user_with_change_permission_holds_change_but_not_delete(
        self, user_with_change_permission
    ):
        user = user_with_change_permission
        assert user.has_perm("change_project", user.project)
        assert not user.has_perm("delete_project", user.project)

    def test_user_with_delete_permission_holds_delete_but_not_change(
        self, user_with_delete_permission
    ):
        user = user_with_delete_permission
        assert user.has_perm("delete_project", user.project)
        assert not user.has_perm("change_project", user.project)

    def test_user_with_no_permission_holds_neither(self, user_with_no_permission):
        user = user_with_no_permission
        assert not user.has_perm("change_project", user.project)
        assert not user.has_perm("delete_project", user.project)
