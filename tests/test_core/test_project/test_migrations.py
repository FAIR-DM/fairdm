"""Tests for individual `fairdm.core.project` migrations."""

import importlib

import pytest
from django.apps import apps as global_apps
from django.db.migrations.state import ProjectState

from fairdm.factories import ProjectFactory, ProjectIdentifierFactory


class TestFundingShapeMigrationIsIrreversible:
    """0008 converts stored funding into DataCite's shape and declares no
    reverse (D-013 in specs/003-core-projects/decisions.md).

    `amount` has no destination in DataCite's schema and is dropped on the
    way in, and a reverse built from `funderName`/`awardNumber` alone would
    also drop `funderIdentifier`, `funderIdentifierType`, `awardTitle` and
    `awardURI` from any record carrying them - and cannot distinguish a
    record this migration produced from a project created directly in the
    new shape afterwards. Declaring no reverse makes a rollback fail loudly
    instead of silently destroying data.
    """

    @staticmethod
    def _operation():
        module = importlib.import_module(
            "fairdm.core.project.migrations.0008_convert_funding_to_datacite_shape"
        )
        return module.Migration.operations[0]

    def test_operation_declares_no_reverse(self):
        assert self._operation().reversible is False

    def test_reversing_the_operation_raises(self):
        with pytest.raises(NotImplementedError):
            self._operation().database_backwards(
                "project", None, ProjectState(), ProjectState()
            )


@pytest.mark.django_db
class TestStrayIdentifierTypesReport:
    """0009 reports (never reassigns or deletes) ProjectIdentifier rows left
    outside the type set 0007 narrowed to (D-013's sibling concern for
    identifiers, FR-011).
    """

    @staticmethod
    def _report_function():
        module = importlib.import_module(
            "fairdm.core.project.migrations.0009_report_stray_identifier_types"
        )
        return module.report_identifiers_outside_narrowed_choices

    def test_stray_identifier_is_left_untouched(self, capsys):
        project = ProjectFactory()
        stray = ProjectIdentifierFactory(related=project, type="ISNI", value="0000")

        self._report_function()(global_apps, None)

        stray.refresh_from_db()
        assert stray.type == "ISNI"
        assert stray.value == "0000"

        captured = capsys.readouterr()
        assert "1 ProjectIdentifier row" in captured.out
        assert "ISNI" in captured.out

    def test_no_stray_identifiers_reports_clean(self, capsys):
        project = ProjectFactory()
        ProjectIdentifierFactory(related=project, type="DOI", value="10.1234/clean")

        self._report_function()(global_apps, None)

        captured = capsys.readouterr()
        assert "database is clean" in captured.out
