"""
Shared fixtures for tests/test_management.
"""

import pytest


@pytest.fixture
def provenance_record():
    """The process-wide provenance record, restored after the test.

    ``fairdm.conf.record`` is one instance for the whole process — the real
    ``tests.settings`` module already populated it once, at import time — so
    a test that rewrites it for its own scenario has to put it back the way
    it found it.
    """
    from fairdm.conf import record

    original = record.layers()
    yield record
    record.replace(original)
