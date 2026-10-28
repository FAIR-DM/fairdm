"""Shared fixtures for Dataset tests."""

import pytest

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.vocabularies import DATE_TYPES, DESCRIPTION_TYPES
from fairdm.factories import (
    ContributionFactory,
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    DatasetLiteratureRelationFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


@pytest.fixture
def public_dataset(db):
    return DatasetFactory(visibility=Visibility.PUBLIC)


@pytest.fixture
def private_dataset(db):
    return DatasetFactory(visibility=Visibility.PRIVATE)


@pytest.fixture
def dataset_with_full_metadata(db):
    dataset = DatasetFactory()
    DatasetDescriptionFactory(related=dataset, type_id=f"{DESCRIPTION_TYPES}/abstract")
    DatasetDateFactory(related=dataset, type_id=f"{DATE_TYPES}/available")
    DatasetIdentifierFactory(related=dataset)
    DatasetLiteratureRelationFactory(dataset=dataset)
    ContributionFactory(content_object=dataset)
    return dataset


@pytest.fixture
def user_with_change_permission(db):
    user = UserFactory()
    user.dataset = DatasetFactory()
    # Editing rights without view is a state no grant path produces: registering gives
    # all five.
    ContributionFactory(
        content_object=user.dataset, contributor=user, level=ContributionLevel.EDIT
    )
    return user


@pytest.fixture
def user_with_delete_permission(db):
    user = UserFactory()
    user.dataset = DatasetFactory()
    ContributionFactory(
        content_object=user.dataset, contributor=user, level=ContributionLevel.MANAGE
    )
    return user


@pytest.fixture
def user_with_no_permission(db):
    user = UserFactory()
    user.dataset = DatasetFactory()
    return user
