"""Shared fixtures for Dataset tests.

Thin wrappers over the factories in ``fairdm.factories``, per constitution
Article X.
"""

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
    """A dataset with PUBLIC visibility."""
    return DatasetFactory(visibility=Visibility.PUBLIC)


@pytest.fixture
def private_dataset(db):
    """A dataset with PRIVATE visibility."""
    return DatasetFactory(visibility=Visibility.PRIVATE)


@pytest.fixture
def dataset_with_full_metadata(db):
    """A dataset carrying one of every related record: a description, a
    date, an identifier, a literature relation and a contribution."""
    dataset = DatasetFactory()
    DatasetDescriptionFactory(related=dataset, type="Abstract")
    DatasetDateFactory(related=dataset, type="Available")
    DatasetIdentifierFactory(related=dataset)
    DatasetLiteratureRelationFactory(dataset=dataset)
    ContributionFactory(content_object=dataset)
    return dataset


@pytest.fixture
def user_with_change_permission(db):
    """A user holding ``change_dataset`` on a dataset of their own, and no
    rights over any other.

    ``view_dataset`` comes with it. A dataset is private by default and its
    pages check visibility, so a holder of editing rights who cannot view
    the record is a state no grant path produces - registering a dataset
    gives its creator all five rights at once. Granting change alone here
    would model a user who cannot exist and would make these tests answer a
    question about a combination the platform never issues. Mirrors
    ``tests/test_core/test_project/conftest.py``'s fixture of the same name.

    The dataset is carried on the returned user as ``.dataset`` - an
    in-memory attribute only, never persisted - so a test can assert the
    grant without also depending on one of the fixtures above.
    """
    user = UserFactory()
    user.dataset = DatasetFactory()
    assign_perm("view_dataset", user, user.dataset)
    assign_perm("change_dataset", user, user.dataset)
    return user


@pytest.fixture
def user_with_delete_permission(db):
    """A user holding ``delete_dataset`` on a dataset of their own, and no
    rights over any other. ``view_dataset`` comes with it, for the reason
    given on ``user_with_change_permission``, which also explains
    ``.dataset``."""
    user = UserFactory()
    user.dataset = DatasetFactory()
    assign_perm("view_dataset", user, user.dataset)
    assign_perm("delete_dataset", user, user.dataset)
    return user


@pytest.fixture
def user_with_no_permission(db):
    """A user holding neither ``change_dataset`` nor ``delete_dataset`` on
    any dataset. See ``user_with_change_permission`` for ``.dataset``."""
    user = UserFactory()
    user.dataset = DatasetFactory()
    return user
