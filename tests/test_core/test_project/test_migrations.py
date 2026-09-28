"""Tests for individual `fairdm.core.project` migrations."""

import importlib

import pytest
from django.db.migrations.state import ProjectState


class TestFundingShapeMigrationIsIrreversible:
    # Reversing 0008 would silently drop `amount` and the other DataCite funder fields,
    # so a rollback has to fail loudly.
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
