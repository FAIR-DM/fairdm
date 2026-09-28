"""Shared fixtures for Dataset tests."""

import pytest
from guardian.shortcuts import assign_perm

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
    DatasetDescriptionFactory(related=dataset, type="Abstract")
    DatasetDateFactory(related=dataset, type="Available")
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
    assign_perm("view_dataset", user, user.dataset)
    assign_perm("change_dataset", user, user.dataset)
    return user


@pytest.fixture
def user_with_delete_permission(db):
    user = UserFactory()
    user.dataset = DatasetFactory()
    assign_perm("view_dataset", user, user.dataset)
    assign_perm("delete_dataset", user, user.dataset)
    return user


@pytest.fixture
def user_with_no_permission(db):
    user = UserFactory()
    user.dataset = DatasetFactory()
    return user
