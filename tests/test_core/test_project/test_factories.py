"""Tests for the project-related factory exports of ``fairdm.factories``."""

import pytest


@pytest.mark.django_db
class TestProjectFixtures:
    def test_user_with_change_permission_holds_change_but_not_delete(
        self, user_with_change_permission
    ):
        user = user_with_change_permission
        assert user.has_perm("change_project", user.project)
        assert not user.has_perm("delete_project", user.project)

    def test_user_with_delete_permission_holds_delete_and_with_it_change(
        self, user_with_delete_permission
    ):
        user = user_with_delete_permission
        assert user.has_perm("delete_project", user.project)
        assert user.has_perm("change_project", user.project)

    def test_user_with_no_permission_holds_neither(self, user_with_no_permission):
        user = user_with_no_permission
        assert not user.has_perm("change_project", user.project)
        assert not user.has_perm("delete_project", user.project)
