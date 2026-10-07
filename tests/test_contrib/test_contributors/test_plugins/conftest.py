"""Fixtures for the contributor pages: a way to request and read a page as a given viewer."""

from types import SimpleNamespace

import pytest
from allauth.socialaccount.models import SocialAccount
from bs4 import BeautifulSoup
from django.test import Client

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility


@pytest.fixture
def get_page():
    """Request a path as a viewer and return the response and its parsed HTML.

    The viewer is a contributor to sign in as, or None for a visitor.
    """

    def get(path, viewer=None):
        browser = Client()
        if viewer is not None:
            browser.force_login(viewer)
        response = browser.get(path)
        return response, BeautifulSoup(response.content.decode(), "html.parser")

    return get


@pytest.fixture
def orcid_signed_in():
    """Record that a person has signed in with ORCID."""

    def connect(person):
        return SocialAccount.objects.create(
            user=person, provider="orcid", uid=f"orcid-{person.pk}"
        )

    return connect


@pytest.fixture
def public_chain(db):
    """A public project, dataset, sample and measurement, one inside the next.

    The sample and measurement are of the demo's registered types.
    """
    project = ProjectFactory(visibility=Visibility.PUBLIC)
    dataset = DatasetFactory(
        project=project, visibility=Visibility.PUBLIC, published=True
    )
    sample = RockSampleFactory(dataset=dataset)
    measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)
    return SimpleNamespace(
        project=project, dataset=dataset, sample=sample, measurement=measurement
    )


@pytest.fixture(params=["project", "dataset", "sample", "measurement"])
def record(request, public_chain):
    """Each kind of record in turn."""
    return getattr(public_chain, request.param)


@pytest.fixture
def manager(record):
    """A person who can sign in and is listed on the record at the manage level."""
    from fairdm.contrib.contributors.choices import ContributionLevel

    person = PersonFactory(is_active=True, is_claimed=True, password="x")
    ContributionFactory(
        content_object=record, contributor=person, level=ContributionLevel.MANAGE
    )
    return person


@pytest.fixture
def reader(record):
    """A person who can sign in and is listed on the record at the view level."""
    from fairdm.contrib.contributors.choices import ContributionLevel

    person = PersonFactory(is_active=True, is_claimed=True, password="x")
    ContributionFactory(
        content_object=record, contributor=person, level=ContributionLevel.VIEW
    )
    return person


@pytest.fixture
def colleague(record):
    """A person already credited on the record, at the view level, with no roles."""
    from fairdm.contrib.contributors.choices import ContributionLevel

    person = PersonFactory(is_active=True, is_claimed=True, password="x")
    return ContributionFactory(
        content_object=record, contributor=person, level=ContributionLevel.VIEW
    )


@pytest.fixture
def partner(record):
    """An organization already credited on the record."""
    return ContributionFactory(
        content_object=record, contributor=OrganizationFactory(), level=None
    )


@pytest.fixture
def newcomer(db):
    """A person in the portal who is credited on nothing."""
    return PersonFactory(is_active=True, is_claimed=True, password="x")


@pytest.fixture
def curator(db):
    """A person who can manage any record through the portal, and is credited on none."""
    return PersonFactory(is_active=True, is_superuser=True, password="x")


@pytest.fixture
def institutes(db):
    """Three organizations a person might be credited from."""
    return SimpleNamespace(
        today=OrganizationFactory(),
        earlier=OrganizationFactory(),
        elsewhere=OrganizationFactory(),
    )


@pytest.fixture
def affiliate(institutes):
    """Give a person a current primary affiliation and an earlier one that has ended."""

    def give(person):
        AffiliationFactory(
            person=person, organization=institutes.today, is_primary=True
        )
        AffiliationFactory(
            person=person,
            organization=institutes.earlier,
            start_date="2015",
            end_date="2019",
        )
        return person

    return give
