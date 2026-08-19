"""
Test fixtures for Sample model tests.

Provides reusable fixtures for testing the Sample model and related functionality.
"""

import pytest
from django.contrib.auth import get_user_model

from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
    SampleDateFactory,
    SampleDescriptionFactory,
    SampleIdentifierFactory,
    SampleRelationFactory,
)
from fairdm.registry import registry

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user.

    ``is_active`` pinned to ``True``: ``PersonFactory`` draws it from
    ``Faker("boolean", chance_of_getting_true=80)`` for realism elsewhere, but an inactive user is
    refused every permission check regardless of what is granted (``guardian.core.ObjectPermissionChecker.has_perm``),
    which made every permission test in this package that expects a grant to hold flake at
    roughly the factory's 1-in-5 rate.
    """
    return PersonFactory(is_active=True)


@pytest.fixture
def project(db):
    """Create a test project."""
    return ProjectFactory()


@pytest.fixture
def dataset(db, project):
    """Create a test dataset linked to a project."""
    return DatasetFactory(project=project)


@pytest.fixture
def rock_sample(db, dataset):
    """Create a test RockSample (polymorphic subclass)."""
    from fairdm_demo.models import RockSample

    return RockSample.objects.create(
        name="Test Rock",
        dataset=dataset,
        rock_type="igneous",
        collection_date="2024-01-15",
    )


@pytest.fixture
def water_sample(db, dataset):
    """Create a test WaterSample (polymorphic subclass)."""
    from fairdm_demo.models import WaterSample

    return WaterSample.objects.create(
        name="Test Water",
        dataset=dataset,
        water_source="river",
        ph_level=7.2,
        temperature_celsius=20.5,
    )


@pytest.fixture
def each_registered_sample_type(db, dataset):
    """One saved specimen of every currently-registered Sample subclass.

    T008. Used by tests that must hold for every registered type rather than one hand-picked
    example - e.g. that querying the base model returns each row as its own type.
    """
    from fairdm_demo.factories import (
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
def sample_with_all_related(db, rock_sample):
    """A specimen carrying one of every related record: description, date, identifier and
    contributor.

    T008.
    """
    SampleDescriptionFactory(related=rock_sample, type="SampleCollection")
    SampleDateFactory(related=rock_sample, type="Created")
    SampleIdentifierFactory(related=rock_sample, type="DOI")
    rock_sample.add_contributor(PersonFactory(), with_roles=["Collection"])
    return rock_sample


@pytest.fixture
def sample_hierarchy_chain(db, dataset):
    """A three-deep provenance chain: grandparent <- parent <- child, each ``child_of`` the
    previous.

    T008.
    """
    from fairdm_demo.factories import RockSampleFactory

    grandparent = RockSampleFactory(dataset=dataset, name="Grandparent")
    parent = RockSampleFactory(dataset=dataset, name="Parent")
    child = RockSampleFactory(dataset=dataset, name="Child")
    SampleRelationFactory(source=parent, target=grandparent, type="child_of")
    SampleRelationFactory(source=child, target=parent, type="child_of")
    return grandparent, parent, child


@pytest.fixture
def clean_registry():
    """Clean the registry before and after each test.

    This ensures tests don't interfere with each other by leaving
    registered models in the registry.
    """
    # Store original state
    original_registry = registry._registry.copy()

    yield

    # Restore original state
    registry._registry = original_registry
