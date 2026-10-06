"""Shared fixtures for the collections listing tests."""

import pytest

from demo.factories import RockSampleFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import ContributionFactory, DatasetFactory, UserFactory


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

    user = UserFactory()
    ContributionFactory(
        content_object=unpublished_dataset,
        contributor=user,
        level=ContributionLevel.EDIT,
    )
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
