"""Fixtures for the autocomplete views, fields and request limits."""

import pytest
from django.contrib.auth.models import Group, Permission

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.sample.models import SampleIdentifier
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteMeasurementFactory, ConcreteSampleFactory


@pytest.fixture
def researcher(db):
    return UserFactory()


@pytest.fixture
def researcher_client(client, researcher):
    client.force_login(researcher)
    return client


@pytest.fixture
def make_dataset(db):
    """Return a function building a dataset, optionally with a level held by one person."""

    def make_dataset(
        name,
        *,
        visibility=Visibility.PRIVATE,
        project_visibility=Visibility.PUBLIC,
        published=False,
        project=None,
        holder=None,
        level=ContributionLevel.EDIT,
    ):
        project = project or ProjectFactory(visibility=project_visibility)
        dataset = DatasetFactory(
            name=name, visibility=visibility, published=published, project=project
        )
        if holder is not None:
            ContributionFactory(content_object=dataset, contributor=holder, level=level)
        return dataset

    return make_dataset


@pytest.fixture
def make_project(db):
    """Return a function building a project, optionally with a level held by one person."""

    def make_project(
        name,
        *,
        visibility=Visibility.PRIVATE,
        holder=None,
        level=ContributionLevel.EDIT,
    ):
        project = ProjectFactory(name=name, visibility=visibility)
        if holder is not None:
            ContributionFactory(content_object=project, contributor=holder, level=level)
        return project

    return make_project


@pytest.fixture
def data_curator(db):
    """Return a person with the portal-wide Data Curator role."""
    person = UserFactory()
    person.groups.add(Group.objects.get(name="Data Curator"))
    return person


@pytest.fixture
def grant_view_everywhere(db):
    """Return a function giving a person the portal-wide right to view every dataset."""

    def grant(person):
        person.user_permissions.add(Permission.objects.get(codename="view_dataset"))

    return grant


@pytest.fixture
def make_record(make_dataset, make_project, make_sample, make_measurement):
    """Return a function building a public record of a kind that one person may edit.

    The record is offered by every address of its kind, whatever the scope.
    """

    def in_public_dataset(name, holder):
        return make_dataset(
            name, visibility=Visibility.PUBLIC, published=True, holder=holder
        )

    def make_record(kind, name, *, holder):
        builders = {
            "project": lambda: make_project(
                name, visibility=Visibility.PUBLIC, holder=holder
            ),
            "dataset": lambda: make_dataset(
                name, visibility=Visibility.PUBLIC, holder=holder
            ),
            "sample": lambda: make_sample(
                name, dataset=in_public_dataset(f"{name} dataset", holder)
            ),
            "measurement": lambda: make_measurement(
                name, dataset=in_public_dataset(f"{name} dataset", holder)
            ),
        }
        return builders[kind]()

    return make_record


@pytest.fixture
def in_request(rf):
    """Return a function that makes a request the current one, as the middleware does.

    A field finds the person through the current request, so a form built in a test is built
    inside one.
    """
    from django_tomselect.middleware import _request_local

    def enter(user, **query):
        request = rf.get("/some/page/", query)
        request.user = user
        _request_local.request = request
        return request

    yield enter
    if hasattr(_request_local, "request"):
        del _request_local.request


@pytest.fixture
def make_sample(db):
    """Return a function building a sample in a dataset, with an optional identifier."""

    def make_sample(name, *, dataset, local_id="", identifier=None):
        sample = ConcreteSampleFactory(name=name, dataset=dataset, local_id=local_id)
        if identifier:
            SampleIdentifier.objects.create(
                related=sample, type="DOI", value=identifier
            )
        return sample

    return make_sample


@pytest.fixture
def make_measurement(db, make_sample):
    """Return a function building a measurement of a new sample in the same dataset."""

    def make_measurement(name, *, dataset, local_id=""):
        sample = make_sample(f"{name} sample", dataset=dataset)
        return ConcreteMeasurementFactory(
            name=name, dataset=dataset, sample=sample, local_id=local_id
        )

    return make_measurement
