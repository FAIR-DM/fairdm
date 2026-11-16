"""Fixtures for the activity tests."""

import pytest
from actstream.models import Action


@pytest.fixture
def clean_slate():
    """Forget every action recorded while the test's records were being built."""

    def wipe():
        Action.objects.all().delete()

    return wipe
