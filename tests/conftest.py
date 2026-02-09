"""
Root-level pytest configuration for FairDM tests.

This conftest.py provides session-level fixtures and configuration that apply
to all tests across all test layers (unit, integration, contract).
"""

import pytest
from django.core.management import call_command


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Session-level database setup.

    Creates test database once per test session and loads required
    reference data that all tests can use.

    The django_db_blocker ensures database access is properly controlled.
    """
    with django_db_blocker.unblock():
        # Load Creative Commons licenses from django-content-license
        call_command("loaddata", "creativecommons", verbosity=0)
