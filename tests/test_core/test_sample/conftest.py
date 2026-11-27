"""Test fixtures for Sample model tests."""

import pytest
from django.contrib.auth import get_user_model

from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
    SampleRelationFactory,
)

User = get_user_model()


@pytest.fixture
def user(db):
    # PersonFactory leaves about 1 in 5 users inactive, and guardian denies an inactive
    # user every object permission.
    return PersonFactory(is_active=True)


@pytest.fixture
def project(db):
    return ProjectFactory()


@pytest.fixture
def dataset(db, project):
    return DatasetFactory(project=project)


@pytest.fixture
def rock_sample(db, dataset):
    from demo.models import RockSample

    return RockSample.objects.create(
        name="Test Rock",
        dataset=dataset,
        rock_type="igneous",
        collection_date="2024-01-15",
    )


@pytest.fixture
def each_registered_sample_type(db, dataset):
    from demo.factories import (
        CustomParentSampleFactory,
        CustomSampleFactory,
        RockSampleFactory,
        SoilSampleFactory,
        WaterSampleFactory,
    )

    factories = [
        RockSampleFactory,
        WaterSampleFactory,
        SoilSampleFactory,
        CustomParentSampleFactory,
        CustomSampleFactory,
    ]
    return [factory(dataset=dataset) for factory in factories]


@pytest.fixture
def sample_hierarchy_chain(db, dataset):
    from demo.factories import RockSampleFactory

    grandparent = RockSampleFactory(dataset=dataset, name="Grandparent")
    parent = RockSampleFactory(dataset=dataset, name="Parent")
    child = RockSampleFactory(dataset=dataset, name="Child")
    SampleRelationFactory(source=parent, target=grandparent, type="child_of")
    SampleRelationFactory(source=child, target=parent, type="child_of")
    return grandparent, parent, child
