"""Shared fixtures for tests/test_management."""

import pytest


@pytest.fixture
def provenance_record():
    from fairdm.conf import record

    original = record.layers()
    yield record
    record.replace(original)
