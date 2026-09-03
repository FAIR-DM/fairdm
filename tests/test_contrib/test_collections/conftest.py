"""Shared fixtures for the collections listing tests.

Thin wrappers over the factories in `fairdm.factories` / `fairdm_demo.factories`, per
constitution Article X.
"""

import pytest

from fairdm.factories import DatasetFactory, UserFactory
from fairdm_demo.factories import RockSampleFactory


@pytest.fixture
def published_dataset(db):
    """A dataset with `published=True`."""
    return DatasetFactory(published=True)


@pytest.fixture
def unpublished_dataset(db):
    """A dataset with `published=False` (the model default)."""
    return DatasetFactory(published=False)


@pytest.fixture
def published_sample(db, published_dataset):
    """A sample belonging to a published dataset."""
    return RockSampleFactory(dataset=published_dataset)


@pytest.fixture
def unpublished_sample(db, unpublished_dataset):
    """A sample belonging to an unpublished dataset."""
    return RockSampleFactory(dataset=unpublished_dataset)


@pytest.fixture
def dataset_owner(db, unpublished_dataset):
    """A signed-in researcher who owns `unpublished_dataset` - the record's owner FR-011
    names as one of the four viewer types a listing must not widen for."""
    from guardian.shortcuts import assign_perm

    user = UserFactory()
    assign_perm("view_dataset", user, unpublished_dataset)
    assign_perm("change_dataset", user, unpublished_dataset)
    return user


@pytest.fixture
def dataset_contributor(db, unpublished_dataset):
    """A contributor credited on `unpublished_dataset`, holding no permission grant of
    their own - distinct from `dataset_owner`."""
    from fairdm.factories import PersonFactory

    person = PersonFactory()
    unpublished_dataset.add_contributor(person)
    return person


@pytest.fixture
def staff_user(db):
    """Portal staff - the fourth viewer type FR-011 names."""
    return UserFactory(is_staff=True)
