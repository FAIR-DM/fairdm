"""Tests for the project-related factory exports (T001).

Covers the package's own export surface (``fairdm/factories/__init__.py``),
not the factory definitions themselves - those already have coverage under
``fairdm/factories/core.py``.
"""

import pytest

from fairdm.core.project.models import Project, ProjectDate
from fairdm.utils.choices import Visibility


class TestProjectRelatedRecordFactoryExports:
    """The package exports all three project related-record factories, the
    same way it already exports the dataset, sample and measurement ones."""

    def test_package_exports_project_description_date_and_identifier_factories(self):
        from fairdm.factories import (
            ProjectDateFactory,
            ProjectDescriptionFactory,
            ProjectIdentifierFactory,
        )

        assert ProjectDescriptionFactory is not None
        assert ProjectDateFactory is not None
        assert ProjectIdentifierFactory is not None

    @pytest.mark.django_db
    def test_project_date_factory_imported_from_the_package_builds_a_project_date(self):
        from fairdm.factories import ProjectDateFactory
        from fairdm.factories.core import ProjectFactory

        project = ProjectFactory()
        date = ProjectDateFactory(related=project)

        assert isinstance(date, ProjectDate)
        assert date.related == project


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
