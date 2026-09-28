"""Shared fixtures for the collections listing tests."""

import pytest

from demo.factories import RockSampleFactory
from fairdm.factories import DatasetFactory, UserFactory


@pytest.fixture
def published_dataset(db):
    return DatasetFactory(published=True)


@pytest.fixture
def unpublished_dataset(db):
    return DatasetFactory(published=False)


@pytest.fixture
def published_sample(db, published_dataset):
    return RockSampleFactory(dataset=published_dataset)


@pytest.fixture
def unpublished_sample(db, unpublished_dataset):
    return RockSampleFactory(dataset=unpublished_dataset)


@pytest.fixture
def dataset_owner(db, unpublished_dataset):
    from guardian.shortcuts import assign_perm

    user = UserFactory()
    assign_perm("view_dataset", user, unpublished_dataset)
    assign_perm("change_dataset", user, unpublished_dataset)
    return user


@pytest.fixture
def dataset_contributor(db, unpublished_dataset):
    from fairdm.factories import PersonFactory

    person = PersonFactory()
    unpublished_dataset.add_contributor(person)
    return person


@pytest.fixture
def staff_user(db):
    return UserFactory(is_staff=True)
