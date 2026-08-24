"""Tests for the project-related factory exports (T001).

Covers the package's own export surface (``fairdm/factories/__init__.py``),
not the factory definitions themselves - those already have coverage under
``fairdm/factories/core.py``.
"""

import pytest

from fairdm.core.project.models import ProjectDate


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
