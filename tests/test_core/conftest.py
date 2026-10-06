"""Fixtures shared by the tests of the core records."""

import pytest

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import ContributionFactory, PersonFactory


@pytest.fixture
def make_manager():
    """Credit a new person who can sign in at the manage level on a record, and return them."""

    def give(record):
        person = PersonFactory(is_active=True, is_claimed=True, password="x")
        ContributionFactory(
            content_object=record, contributor=person, level=ContributionLevel.MANAGE
        )
        return person

    return give
