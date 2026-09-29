"""Shared fixtures for Project tests."""

import pytest
from guardian.shortcuts import assign_perm

from fairdm.factories import ProjectFactory, UserFactory
from fairdm.utils.choices import Visibility


@pytest.fixture
def public_project(db):
    return ProjectFactory(visibility=Visibility.PUBLIC)


@pytest.fixture
def private_project(db):
    return ProjectFactory(visibility=Visibility.PRIVATE)


@pytest.fixture
def user_with_change_permission(db):
    user = UserFactory()
    user.project = ProjectFactory()
    # Editing rights without view is a state no grant path produces: registering gives
    # all five.
    assign_perm("view_project", user, user.project)
    assign_perm("change_project", user, user.project)
    return user


@pytest.fixture
def user_with_delete_permission(db):
    user = UserFactory()
    user.project = ProjectFactory()
    assign_perm("view_project", user, user.project)
    assign_perm("delete_project", user, user.project)
    return user


@pytest.fixture
def user_with_no_permission(db):
    user = UserFactory()
    user.project = ProjectFactory()
    return user


@pytest.fixture
def overview_showcase(db):
    """A public project holding public, public-unpublished and private datasets.

    The private dataset carries the only soil samples, the only ICP-MS measurements and the only
    CC0 licence, so anything of theirs on a visitor's page is a leak.
    """
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from licensing.models import License

    from demo.factories import (
        ICP_MS_MeasurementFactory,
        RockSampleFactory,
        SoilSampleFactory,
        WaterSampleFactory,
        XRFMeasurementFactory,
    )
    from fairdm.factories import DatasetFactory, PersonFactory

    project = ProjectFactory(visibility=Visibility.PUBLIC, status=2)
    leaders = [
        PersonFactory(name="Leader One", is_active=True),
        PersonFactory(name="Leader Two", is_active=True),
    ]
    for leader in leaders:
        project.add_contributor(leader, with_roles=["ProjectLeader", "Creator"])
    others = [PersonFactory(name=f"Other {n:02d}", is_active=True) for n in range(20)]
    for person in others:
        project.add_contributor(person, with_roles=["Other"])

    cc0 = License.objects.get(name="CC0 1.0")
    published = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=True
    )
    unpublished = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=False
    )
    private = DatasetFactory(
        project=project, visibility=Visibility.PRIVATE, published=False, license=cc0
    )

    rocks = RockSampleFactory.create_batch(2, dataset=published)
    XRFMeasurementFactory.create_batch(2, dataset=published, sample=rocks[0])
    WaterSampleFactory(dataset=unpublished)
    soils = SoilSampleFactory.create_batch(3, dataset=private)
    ICP_MS_MeasurementFactory(dataset=private, sample=soils[0])

    from fairdm.core.measurement.models import Measurement
    from fairdm.core.sample.models import Sample

    # Two months apart, so the running total has a shape to draw.
    Sample.objects.filter(pk__in=[s.pk for s in rocks]).update(
        added=datetime(2026, 1, 15, tzinfo=UTC)
    )
    Sample.objects.exclude(pk__in=[s.pk for s in rocks]).update(
        added=datetime(2026, 3, 15, tzinfo=UTC)
    )
    Measurement.objects.update(added=datetime(2026, 2, 15, tzinfo=UTC))

    return SimpleNamespace(
        project=project,
        leaders=leaders,
        others=others,
        published=published,
        unpublished=unpublished,
        private=private,
    )


@pytest.fixture
def project_team_member(db, overview_showcase):
    """A signed-in user who may change the showcase project."""
    user = UserFactory()
    assign_perm("view_project", user, overview_showcase.project)
    assign_perm("change_project", user, overview_showcase.project)
    return user
