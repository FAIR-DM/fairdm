"""Shared fixtures for Dataset tests.

Thin wrappers over the factories in ``fairdm.factories``, per constitution
Article X.
"""

import pytest

from fairdm.factories import (
    ContributionFactory,
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    DatasetLiteratureRelationFactory,
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
