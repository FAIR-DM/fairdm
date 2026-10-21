"""Fixtures for the autocomplete views, fields and request limits."""

import pytest
from django.contrib.auth.models import Group, Permission

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


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
        project=None,
        holder=None,
        level=ContributionLevel.EDIT,
    ):
        project = project or ProjectFactory(visibility=project_visibility)
        dataset = DatasetFactory(name=name, visibility=visibility, project=project)
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
def make_record(make_dataset, make_project):
    """Return a function building a public record of a kind that one person may edit.

    The record is offered by every address of its kind, whatever the scope.
    """

    def make_record(kind, name, *, holder):
        builders = {"project": make_project, "dataset": make_dataset}
        return builders[kind](name, visibility=Visibility.PUBLIC, holder=holder)

    return make_record
