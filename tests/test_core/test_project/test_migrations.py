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
